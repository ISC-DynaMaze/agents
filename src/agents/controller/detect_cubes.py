from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from spade.behaviour import OneShotBehaviour

from common.models.camera import CameraRequest, CameraResponse
from common.models.common import ReqResAdapter
from common.models.controller import CubesResponse
from common.sender import BaseSenderBehaviour

if TYPE_CHECKING:
    from agents.controller.agent import ControllerAgent


class DetectCubesBehaviour(OneShotBehaviour):
    agent: ControllerAgent

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("DetectCubesBehaviour")

    async def on_start(self):
        self.logger = self.agent.logger
        self.cubes_dir = Path("cubes")

    async def run(self):
        self.cubes_dir.mkdir(parents=True, exist_ok=True)

        await self.req_image()
        img = await self.wait_for_new_image(timeout=10.0)

        black_mask, cubes = self.detect_cubes(img)

        self.store_cubes_in_maze(cubes)

        for cube in cubes:
            self.logger.info(f"Detected black cube: {cube}")

        highlighted = self.draw_cubes(img, cubes)

        await self.save_img(black_mask, self.cubes_dir, prefix="cubes_mask")
        await self.save_img(highlighted, self.cubes_dir, prefix="cubes_detected")

        await self.send_cubes_response()

    def detect_cubes(self, img: np.ndarray):
        if self.agent.maze.rect is None:
            raise ValueError("Maze must be built before detecting cubes")

        # crop to maze area
        rect_x, rect_y, rect_w, rect_h = self.agent.maze.rect
        maze_img = img[rect_y : rect_y + rect_h, rect_x : rect_x + rect_w]

        gray = cv2.cvtColor(maze_img, cv2.COLOR_BGR2GRAY)
        black_mask = self.get_black_cube_mask(gray)

        cubes = self.extract_cubes_from_mask(
            mask=black_mask,
            offset=(rect_x, rect_y),
        )

        full_black_mask = np.zeros(img.shape[:2], dtype=np.uint8)
        full_black_mask[rect_y : rect_y + rect_h, rect_x : rect_x + rect_w] = black_mask

        return full_black_mask, cubes

    def get_black_cube_mask(self, gray: np.ndarray):
        mask = cv2.inRange(gray, 0, 40)
        return mask

    def extract_cubes_from_mask(
        self,
        mask: np.ndarray,
        offset: tuple[int, int],
        min_area: int = 6,
        max_area: int = 400,
    ):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        offset_x, offset_y = offset
        cubes = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area or area > max_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)

            if w < 3 or h < 3:
                continue

            if w > 30 or h > 30:
                continue

            aspect_ratio = w / float(h)
            if aspect_ratio < 0.45 or aspect_ratio > 2.2:
                continue

            extent = area / float(w * h)
            if extent < 0.30:
                continue

            center_x = offset_x + x + w // 2
            center_y = offset_y + y + h // 2

            # convert to cell coordinates
            row, col = self.agent.maze.pixel_to_cell(center_x, center_y)
            self.agent.info(f"Detected cube at cell : {row}, {col}")
            if not self.agent.maze.is_valid_cell(row, col):
                continue

            # determine which side of the cell the cube is closest to
            side = self.get_cube_side_in_cell(
                center=(center_x, center_y),
                row=row,
                col=col,
            )
            self.agent.info(f"Cube at cell {row}, {col} is closest to side: {side}")

            cubes.append(
                {
                    "bbox": (offset_x + x, offset_y + y, w, h),
                    "center": (center_x, center_y),
                    "row": row,
                    "col": col,
                    "side": side,
                    "area": area,
                }
            )

        return cubes

    def get_cube_side_in_cell(
        self,
        center: tuple[int, int],
        row: int,
        col: int,
    ):
        rect_x, rect_y, rect_w, rect_h = self.agent.maze.rect

        cell_w = rect_w / self.agent.maze.n_cols
        cell_h = rect_h / self.agent.maze.n_rows

        cx, cy = center

        cell_x1 = rect_x + col * cell_w
        cell_y1 = rect_y + row * cell_h
        cell_x2 = cell_x1 + cell_w
        cell_y2 = cell_y1 + cell_h

        distances = {
            "up": abs(cy - cell_y1),
            "right": abs(cell_x2 - cx),
            "down": abs(cell_y2 - cy),
            "left": abs(cx - cell_x1),
        }

        return min(distances, key=distances.get)

    def store_cubes_in_maze(self, cubes: list[dict]):
        # Store globally on maze.
        self.agent.maze.clear_cubes()

        for cube in cubes:
            self.agent.maze.add_cube(cube)

    # draw function for visualization
    def draw_cubes(self, img: np.ndarray, cubes: list[dict]):
        highlighted = img.copy()

        for cube in cubes:
            x, y, w, h = cube["bbox"]

            box_color = (0, 0, 255)

            cv2.rectangle(highlighted, (x, y), (x + w, y + h), box_color, 2)

        return highlighted

    async def send_cubes_response(self):
        res = CubesResponse()

        for requester in self.agent.cubes_requesters:
            self.agent.add_behaviour(BaseSenderBehaviour(res, requester))

        self.agent.cubes_requesters = []
        self.agent.requesting_cubes = False

    async def req_image(self):
        req = CameraRequest()
        self.agent.add_behaviour(BaseSenderBehaviour(req, str(self.agent.camera_jid)))

    async def wait_for_new_image(self, timeout: float) -> np.ndarray:
        while True:
            try:
                msg = await self.receive(timeout=timeout)
                if msg is None:
                    self.logger.error("Timed out waiting for camera response message")
                    continue
                res = ReqResAdapter.validate_json(msg.body)
                assert isinstance(res, CameraResponse)
                save_dir = Path("photos")
                img, _ = await res.decode_img(save_dir)
                return img
            except Exception as e:
                self.logger.error(
                    f"Error occurred while waiting for camera response: {e}"
                )
                continue

    async def save_img(self, img: np.ndarray, save_dir: Path, prefix: str) -> None:
        self.logger.info(f"Saving image to {save_dir}")
        timestamp = int(time.time())
        img_path = save_dir / f"{prefix}_{timestamp}.jpg"
        cv2.imwrite(str(img_path), img)
