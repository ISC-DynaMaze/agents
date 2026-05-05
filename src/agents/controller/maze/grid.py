import os

import cv2 as cv
import numpy as np

DEBUG = os.environ.get("MAZE_DEBUG", "0") != "0"

# wall indices
UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3


class Cell:
    def __init__(self, row, col, walls=None):
        self.row = row
        self.col = col
        self.walls = walls if walls is not None else [False, False, False, False]
        self.obstacles = []

        # for astar search
        self.f = float("inf")  # Total cost of the cell (g + h)
        self.g = float("inf")  # Cost from start to this cell
        self.h = 0  # Heuristic cost from this cell to destination
        self.parent = None  # Parent cell for path tracing

    def add_wall(self, position):
        self.walls[position] = True

    def has_wall(self, position):
        return self.walls[position]

    def add_obstacle(self, obstacle):
        self.obstacles.append(obstacle)

    def clear_pathfinding_info(self):
        self.f = float("inf")
        self.g = float("inf")
        self.h = 0
        self.parent = None

    def __repr__(self):
        return f"Cell({self.row}, {self.col}, walls={self.walls})"


class Maze:
    def __init__(self, rows, cols):
        self.n_rows = rows
        self.n_cols = cols

        # grid of cells
        self.grid = [[Cell(i, j) for j in range(cols)] for i in range(rows)]

        # bot and target cells
        self.bot_cell = self.grid[0][0]
        self.target_cell = self.grid[rows - 1][cols - 1]

        # explicit wall maps
        # horizontal walls: (rows + 1) x cols
        self.h_walls = [[False for _ in range(cols)] for _ in range(rows + 1)]

        # vertical walls: rows x (cols + 1)
        self.v_walls = [[False for _ in range(cols + 1)] for _ in range(rows)]

        # maze rectangle in source image coordinates: (x, y, w, h)
        self.rect = None

        # list of detected obstacles
        self.obstacles = []

    # check if a cell is within boundaries
    # should return true if valid cell
    def is_valid_cell(self, row, col):
        return 0 <= row < self.n_rows and 0 <= col < self.n_cols

    # return cell at given row, check if it is a valid cell
    def get_cell(self, row, col):
        if self.is_valid_cell(row, col):
            return self.grid[row][col]
        else:
            # if cell not valid
            return None

    def add_obstacle(self, obstacle):
        self.obstacles.append(obstacle)
        for cell in obstacle.cells:
            cell.add_obstacle(obstacle)

    # check if a move is valid (no wall blocking and destination in bounds)
    # move: 0=DOWN, 1=UP, 2=RIGHT, 3=LEFT
    def is_valid_move(self, row, col, move):
        if not self.is_valid_cell(row, col):
            return False

        current_cell = self.grid[row][col]

        # Calculate destination based on move direction
        if move == 0:  # DOWN
            new_row, new_col = row + 1, col
            wall_direction = DOWN
        elif move == 1:  # UP
            new_row, new_col = row - 1, col
            wall_direction = UP
        elif move == 2:  # RIGHT
            new_row, new_col = row, col + 1
            wall_direction = RIGHT
        elif move == 3:  # LEFT
            new_row, new_col = row, col - 1
            wall_direction = LEFT
        else:
            return False

        # Check if destination is within bounds
        if not self.is_valid_cell(new_row, new_col):
            return False

        # Check if there's a wall blocking this direction
        if current_cell.has_wall(wall_direction):
            return False

        return True

    # add a wall to the cell and update neighboring cell's wall as well
    def add_wall(self, row, col, direction):
        if not self.is_valid_cell(row, col):
            return

        self.grid[row][col].add_wall(direction)

        if direction == UP:
            self.h_walls[row][col] = True
            neighbor_row, neighbor_col = row - 1, col
            opposite = DOWN

        elif direction == RIGHT:
            self.v_walls[row][col + 1] = True
            neighbor_row, neighbor_col = row, col + 1
            opposite = LEFT

        elif direction == DOWN:
            self.h_walls[row + 1][col] = True
            neighbor_row, neighbor_col = row + 1, col
            opposite = UP

        elif direction == LEFT:
            self.v_walls[row][col] = True
            neighbor_row, neighbor_col = row, col - 1
            opposite = RIGHT

        else:
            return

        if self.is_valid_cell(neighbor_row, neighbor_col):
            self.grid[neighbor_row][neighbor_col].add_wall(opposite)

    # clear all walls from the maze
    def clear_walls(self):
        self.h_walls = [
            [False for _ in range(self.n_cols)] for _ in range(self.n_rows + 1)
        ]
        self.v_walls = [
            [False for _ in range(self.n_cols + 1)] for _ in range(self.n_rows)
        ]

        for row in range(self.n_rows):
            for col in range(self.n_cols):
                self.grid[row][col].walls = [False, False, False, False]

    # add outer border walls to the maze
    def add_outer_border(self):
        # top and bottom borders
        for col in range(self.n_cols):
            self.h_walls[0][col] = True
            self.h_walls[self.n_rows][col] = True

        # left and right borders
        for row in range(self.n_rows):
            self.v_walls[row][0] = True
            self.v_walls[row][self.n_cols] = True

        # update cell wall flags too
        for col in range(self.n_cols):
            self.grid[0][col].add_wall(UP)
            self.grid[self.n_rows - 1][col].add_wall(DOWN)

        for row in range(self.n_rows):
            self.grid[row][0].add_wall(LEFT)
            self.grid[row][self.n_cols - 1].add_wall(RIGHT)

    # detect target cell with aruco marker
    def detect_aruco_markers(self, image):
        dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_100)
        params = cv.aruco.DetectorParameters()
        detector = cv.aruco.ArucoDetector(dict, params)

        corners, ids, rejected = detector.detectMarkers(image)

        if len(corners) > 0:
            # if DEBUG:
            #     img2 = image.copy()
            #     cv.aruco.drawDetectedMarkers(img2, corners, ids)
            #     cv.imshow("marker.png", img2)
            print(f"Detected Aruco marker IDs: {ids.flatten()}")
        else:
            print("No Aruco markers detected")

        return corners, ids, rejected

    # set target cell as the aruco marker (should stay the same throughout the whole process)
    def set_target_cell(self, corners, ids, target_id):
        if ids is None:
            print("No Aruco markers detected, cannot set target cell")
            return

        for i, marker_id in enumerate(ids.flatten()):
            if marker_id == target_id:
                # get the center of the marker
                c = corners[i][0]
                center_x = int(c[:, 0].mean())
                center_y = int(c[:, 1].mean())

                # convert pixel coordinates to cell coordinates
                row, col = self.pixel_to_cell(center_x, center_y)

                if self.is_valid_cell(row, col):
                    self.target_cell = self.grid[row][col]
                    print(
                        f"Set target cell to {self.target_cell} based on Aruco marker ID {target_id}"
                    )
                else:
                    print(f"Aruco marker ID {target_id} is out of maze bounds")
                return

        print(f"Aruco marker ID {target_id} not found, cannot set target cell")

    # set bot marker (can move; we can call this multiple times to update target position in find_path)
    def set_bot_cell(self, corners, ids, bot_id):
        if ids is None:
            print("No Aruco markers detected, cannot set bot cell")
            return

        for i, marker_id in enumerate(ids.flatten()):
            if marker_id == bot_id:
                # get the center of the marker
                c = corners[i][0]
                center_x = int(c[:, 0].mean())
                center_y = int(c[:, 1].mean())

                # convert pixel coordinates to cell coordinates
                row, col = self.pixel_to_cell(center_x, center_y)

                if self.is_valid_cell(row, col):
                    self.bot_cell = self.grid[row][col]
                    print(
                        f"Set bot cell to {self.bot_cell} based on Aruco marker ID {bot_id}"
                    )
                else:
                    print(f"Aruco marker ID {bot_id} is out of maze bounds")
                return

        print(f"Aruco marker ID {bot_id} not found, cannot set bot cell")

    def clear_pathfinding_info(self):
        for row in self.grid:
            for cell in row:
                cell.clear_pathfinding_info()

    # helper functions for building maze from detected lines

    def _clamp(self, value, low, high):
        return max(low, min(high, value))

    def _snap_x_to_col_boundary(self, x, rect_x, cell_w):
        return int(round((x - rect_x) / cell_w))

    def _snap_y_to_row_boundary(self, y, rect_y, cell_h):
        return int(round((y - rect_y) / cell_h))

    def _overlap_length(self, a1, a2, b1, b2):
        left = max(a1, b1)
        right = min(a2, b2)
        return max(0, right - left)

    # build maze walls from detected pixel segments
    # overlap_ratio: minimum fraction of a cell boundary that must be covered to mark that wall as present
    def build_from_detected_lines(
        self, rect, horizontal_lines, vertical_lines, overlap_ratio=0.6
    ):
        self.clear_walls()
        self.add_outer_border()

        # keep rectangle for coordinate transforms (e.g. ArUco marker center -> maze cell)
        self.rect = rect

        # dimensions of the main rectangle containing the maze
        rect_x, rect_y, rect_w, rect_h = rect
        cell_w = rect_w / self.n_cols
        cell_h = rect_h / self.n_rows

        # horizontal lines -> h_walls
        for x1, y, x2, _ in horizontal_lines:
            if x2 < x1:
                x1, x2 = x2, x1

            # snap y to nearest row boundary
            row_boundary = self._snap_y_to_row_boundary(y, rect_y, cell_h)
            row_boundary = self._clamp(row_boundary, 0, self.n_rows)

            # check overlap with each cell boundary in that row
            for col in range(self.n_cols):
                cell_x1 = rect_x + col * cell_w
                cell_x2 = rect_x + (col + 1) * cell_w

                overlap = self._overlap_length(x1, x2, cell_x1, cell_x2)
                cell_width = cell_x2 - cell_x1

                # if overlap is large enough, mark the wall as present
                if overlap >= overlap_ratio * cell_width:
                    self.h_walls[row_boundary][col] = True

                    if row_boundary > 0:
                        self.grid[row_boundary - 1][col].add_wall(DOWN)
                    if row_boundary < self.n_rows:
                        self.grid[row_boundary][col].add_wall(UP)

        # vertical lines -> v_walls
        for x, y1, _, y2 in vertical_lines:
            if y2 < y1:
                y1, y2 = y2, y1

            col_boundary = self._snap_x_to_col_boundary(x, rect_x, cell_w)
            col_boundary = self._clamp(col_boundary, 0, self.n_cols)

            for row in range(self.n_rows):
                cell_y1 = rect_y + row * cell_h
                cell_y2 = rect_y + (row + 1) * cell_h

                overlap = self._overlap_length(y1, y2, cell_y1, cell_y2)
                cell_height = cell_y2 - cell_y1

                if overlap >= overlap_ratio * cell_height:
                    self.v_walls[row][col_boundary] = True

                    if col_boundary > 0:
                        self.grid[row][col_boundary - 1].add_wall(RIGHT)
                    if col_boundary < self.n_cols:
                        self.grid[row][col_boundary].add_wall(LEFT)

    # draw the maze grid with walls and cell labels for visualization
    def draw(self, cell_size=100, margin=40, wall_thickness=3):
        # calculate image size
        img_h = self.n_rows * cell_size + 2 * margin
        img_w = self.n_cols * cell_size + 2 * margin

        img = np.ones((img_h, img_w, 3), dtype=np.uint8) * 255

        # light cell grid + labels
        for row in range(self.n_rows):
            for col in range(self.n_cols):
                x1 = margin + col * cell_size
                y1 = margin + row * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size

                cv.rectangle(img, (x1, y1), (x2, y2), (220, 220, 220), 1)

                label = f"{row},{col}"
                cv.putText(
                    img,
                    label,
                    (x1 + 12, y1 + cell_size // 2),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (150, 150, 150),
                    1,
                    cv.LINE_AA,
                )

        # horizontal walls
        for r in range(self.n_rows + 1):
            for c in range(self.n_cols):
                if self.h_walls[r][c]:
                    x1 = margin + c * cell_size
                    x2 = margin + (c + 1) * cell_size
                    y = margin + r * cell_size
                    cv.line(img, (x1, y), (x2, y), (0, 180, 0), wall_thickness)

        # vertical walls
        for r in range(self.n_rows):
            for c in range(self.n_cols + 1):
                if self.v_walls[r][c]:
                    x = margin + c * cell_size
                    y1 = margin + r * cell_size
                    y2 = margin + (r + 1) * cell_size
                    cv.line(img, (x, y1), (x, y2), (0, 0, 255), wall_thickness)

        return img

    # pixel to cell coordinates
    def pixel_to_cell(self, x, y, cell_size=140, margin=40):
        # using detected maze rectangle.
        if self.rect is not None:
            rect_x, rect_y, rect_w, rect_h = self.rect
            cell_w = rect_w / self.n_cols
            cell_h = rect_h / self.n_rows

            col = int((x - rect_x) / cell_w)
            row = int((y - rect_y) / cell_h)
            return row, col

        col = int((x - margin) // cell_size)
        row = int((y - margin) // cell_size)
        return row, col

    # convert maze to a dictionary format for easy serialization
    def to_dict(self):
        return {
            "rows": self.n_rows,
            "cols": self.n_cols,
            "cells": [
                [
                    {"row": cell.row, "col": cell.col, "walls": cell.walls}
                    for cell in row
                ]
                for row in self.grid
            ],
        }

    # create a maze object from a dictionary
    @classmethod
    def from_dict(cls, data):
        maze = cls(rows=data["rows"], cols=data["cols"])
        maze.clear_walls()

        for row in range(maze.n_rows):
            for col in range(maze.n_cols):
                cell_data = data["cells"][row][col]
                maze.grid[row][col].walls = cell_data["walls"][:]

        # rebuild h_walls and v_walls from cells
        maze.h_walls = [
            [False for _ in range(maze.n_cols)] for _ in range(maze.n_rows + 1)
        ]
        maze.v_walls = [
            [False for _ in range(maze.n_cols + 1)] for _ in range(maze.n_rows)
        ]

        for row in range(maze.n_rows):
            for col in range(maze.n_cols):
                cell = maze.grid[row][col]

                if cell.has_wall(UP):
                    maze.h_walls[row][col] = True
                if cell.has_wall(DOWN):
                    maze.h_walls[row + 1][col] = True
                if cell.has_wall(LEFT):
                    maze.v_walls[row][col] = True
                if cell.has_wall(RIGHT):
                    maze.v_walls[row][col + 1] = True

        return maze

    def print_maze(self):
        for row in self.grid:
            for cell in row:
                print(cell)
