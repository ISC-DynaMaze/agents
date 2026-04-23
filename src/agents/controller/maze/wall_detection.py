import os

import cv2 as cv
import numpy as np

from agents.controller.maze.grid import Maze

DEBUG = os.environ.get("MAZE_DEBUG", "0") != "0"


def get_image(image_path):
    img = cv.imread(str(image_path), cv.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Error opening image: {image_path}")
    return img


# get a pink mask from the image using HSV color space -> binary image with white walls and black background
def get_pink_mask(image):
    # use LAB color space for better color segmentation
    lab = cv.cvtColor(image, cv.COLOR_BGR2LAB)
    L, a, b = cv.split(lab)

    # 'a' channel = green <-> red
    a = a.astype(np.uint8)
    b = b.astype(np.uint8)

    # dynamic threshold: keep reddish pixels
    a_thresh = max(145, int(np.percentile(a, 92)))

    # reject yellowish pixels (maze walls and floor)
    b_thresh = int(np.percentile(b, 85))

    color_mask = np.zeros_like(a, dtype=np.uint8)
    color_mask[(a >= a_thresh) & (b <= b_thresh + 10)] = 255

    # small cleanup
    small_kernel = np.ones((3, 3), np.uint8)
    color_mask = cv.morphologyEx(color_mask, cv.MORPH_OPEN, small_kernel, iterations=1)

    # keep only long thin horizontal / vertical structures
    horiz_kernel = cv.getStructuringElement(cv.MORPH_RECT, (25, 1))
    vert_kernel = cv.getStructuringElement(cv.MORPH_RECT, (1, 25))

    horiz = cv.morphologyEx(color_mask, cv.MORPH_OPEN, horiz_kernel)
    vert = cv.morphologyEx(color_mask, cv.MORPH_OPEN, vert_kernel)

    mask = cv.bitwise_or(horiz, vert)

    # reconnect tiny gaps in the wall lines
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, small_kernel, iterations=2)

    return mask


# get main rectangle of maze
# count white pixels in each column and row
# find the first and last column/row that have a significant number of white pixels to determine the bounding rectangle of the maze
def find_outer_rectangle(mask, min_pixels_ratio=0.2):
    h, w = mask.shape

    # count white pixels in each column and row
    col_counts = np.count_nonzero(mask > 0, axis=0)
    row_counts = np.count_nonzero(mask > 0, axis=1)

    # treshold depends on the size of image
    col_threshold = int(h * min_pixels_ratio)
    row_threshold = int(w * min_pixels_ratio)

    xs = np.where(col_counts > col_threshold)[0]
    ys = np.where(row_counts > row_threshold)[0]

    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("could not find outer rectangle")

    x_min = xs[0]
    x_max = xs[-1]
    y_min = ys[0]
    y_max = ys[-1]

    return (x_min, y_min, x_max - x_min, y_max - y_min)


# keep only lines that are in the main rectangle
def keep_lines_in_rectangle(lines, rect, margin=10):
    x, y, w, h = rect

    x_min = x - margin
    y_min = y - margin
    x_max = x + w + margin
    y_max = y + h + margin

    kept_lines = []

    for x1, y1, x2, y2 in lines:
        if (
            x_min <= x1 <= x_max
            and x_min <= x2 <= x_max
            and y_min <= y1 <= y_max
            and y_min <= y2 <= y_max
        ):
            kept_lines.append((x1, y1, x2, y2))

    return kept_lines


# mask with horizontal lines
def extract_horizontal_mask(mask, kernel_len=25):
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (kernel_len, 1))
    horizontal = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)
    return horizontal


# mask with vertical lines
def extract_vertical_mask(mask, kernel_len=25):
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (1, kernel_len))
    vertical = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)
    return vertical


# get horizontal segments as (x1, y, x2, y) from horizontal mask, filter by min_length
def get_horizontal_segments(horizontal_mask, min_length=30):
    contours, _ = cv.findContours(
        horizontal_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
    )

    segments = []

    for cnt in contours:
        x, y, w, h = cv.boundingRect(cnt)

        if w >= min_length:
            y_center = y + h // 2
            segments.append((x, y_center, x + w, y_center))

    segments.sort(key=lambda line: (line[1], line[0]))
    return segments


# get vertical segments as (x, y1, x, y2) from vertical mask, filter by min_length
def get_vertical_segments(vertical_mask, min_length=30):
    contours, _ = cv.findContours(
        vertical_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
    )

    segments = []

    for cnt in contours:
        x, y, w, h = cv.boundingRect(cnt)

        if h >= min_length:
            x_center = x + w // 2
            segments.append((x_center, y, x_center, y + h))

    segments.sort(key=lambda line: (line[0], line[1]))
    return segments


# draw main rectangle on img
def draw_outer_rectangle(img, rect):
    x, y, w, h = rect
    cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 3)
    return img


# draw lines on img
def draw_lines(img, horizontal, vertical):
    # horizontal in green
    for x1, y1, x2, y2 in horizontal:
        cv.line(img, (x1, y1), (x2, y2), (0, 255, 0), 3)

    # vertical in red
    for x1, y1, x2, y2 in vertical:
        cv.line(img, (x1, y1), (x2, y2), (0, 0, 255), 3)

    return img


# main function to detect maze walls from an image already loaded in memory
def detect_maze_walls_from_image(image, kernel_len=25, min_length=30):
    mask = get_pink_mask(image)

    # contours of maze
    rect = find_outer_rectangle(mask)

    # masks for horizontal and vertical lines
    horizontal_mask = extract_horizontal_mask(mask, kernel_len=kernel_len)
    vertical_mask = extract_vertical_mask(mask, kernel_len=kernel_len)

    # segments of horizontal and vertical lines
    horizontal_lines = get_horizontal_segments(horizontal_mask, min_length=min_length)
    vertical_lines = get_vertical_segments(vertical_mask, min_length=min_length)

    # filter lines to keep only those in the main rectangle
    horizontal_lines = keep_lines_in_rectangle(horizontal_lines, rect)
    vertical_lines = keep_lines_in_rectangle(vertical_lines, rect)

    return rect, horizontal_lines, vertical_lines, mask, horizontal_mask, vertical_mask


# convenient function for behaviours
def build_maze_from_image(
    image,
    rows=3,
    cols=11,
    kernel_len=25,
    min_length=30,
    overlap_ratio=0.6,
    cell_size=140,
    margin=40,
    wall_thickness=4,
):
    rect, horizontal_lines, vertical_lines, mask, horizontal_mask, vertical_mask = (
        detect_maze_walls_from_image(
            image=image,
            kernel_len=kernel_len,
            min_length=min_length,
        )
    )

    maze = Maze(rows=rows, cols=cols)
    maze.build_from_detected_lines(
        rect, horizontal_lines, vertical_lines, overlap_ratio=overlap_ratio
    )

    ## detect aruco target and bot markers
    corners, ids, rejected = maze.detect_aruco_markers(image)
    maze.set_target_cell(corners, ids)
    maze.set_bot_cell(corners, ids)

    print(f"Maze target cell: {maze.target_cell}")
    print(f"Maze bot cell: {maze.bot_cell}")

    grid_img = maze.draw(
        cell_size=cell_size,
        margin=margin,
        wall_thickness=wall_thickness,
    )

    debug_img = image.copy()
    debug_img = draw_outer_rectangle(debug_img, rect)
    debug_img = draw_lines(debug_img, horizontal_lines, vertical_lines)
    if DEBUG:
        cv.imshow("outer rectangle", debug_img)

    return {
        "maze": maze,
        "grid_img": grid_img,
        "debug_img": debug_img,
        "mask": mask,
        "horizontal_mask": horizontal_mask,
        "vertical_mask": vertical_mask,
        "rect": rect,
        "horizontal_lines": horizontal_lines,
        "vertical_lines": vertical_lines,
    }


def build_maze_from_path(
    image_path,
    rows=3,
    cols=11,
    kernel_len=25,
    min_length=30,
    overlap_ratio=0.6,
    cell_size=140,
    margin=40,
    wall_thickness=4,
):
    image = get_image(image_path)
    return build_maze_from_image(
        image=image,
        rows=rows,
        cols=cols,
        kernel_len=kernel_len,
        min_length=min_length,
        overlap_ratio=overlap_ratio,
        cell_size=cell_size,
        margin=margin,
        wall_thickness=wall_thickness,
    )
