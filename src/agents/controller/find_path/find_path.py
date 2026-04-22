import os

import cv2 as cv

from agents.controller.walls.grid import Maze
from agents.controller.walls.wall_detection import build_maze_from_path

DEBUG = os.environ.get("MAZE_DEBUG", "0") != "0"


def set_bot_cell(maze, row, col):
    maze.bot_cell = maze.grid[row][col]


def set_target_cell(maze, row, col):
    maze.target_cell = maze.grid[row][col]


#### Helper functions for A* search
# Check if a cell is the destination
def is_destination(row, col, dest):
    return row == dest[0] and col == dest[1]


# Calculate the heuristic value of a cell (Euclidean distance to destination)
def calculate_h_value(row, col, dest):
    return ((row - dest[0]) ** 2 + (col - dest[1]) ** 2) ** 0.5


# trace path
def trace_path(maze, dest_cell):
    path = []
    current_cell = dest_cell

    while current_cell is not None:
        path.append((current_cell.row, current_cell.col))
        current_cell = current_cell.parent

    path.reverse()

    return path[::-1]  # Return reversed path


# print path on console
def print_path(path):
    for i in path:
        print("->", i, end=" ")
    print()


# a* search algorithm
def a_star_search(maze, src, dest):
    # Check if the source and destination are valid
    if not maze.is_valid_cell(src[0], src[1]) or not maze.is_valid_cell(
        dest[0], dest[1]
    ):
        print("Source or destination is invalid")
        return

    # Check if we are already at the destination
    if is_destination(src[0], src[1], dest):
        print("We are already at the destination")
        return

    found_dest = False

    # Initialize the open list and closed list
    open_list = []
    closed_list = [[False for _ in range(maze.n_cols)] for _ in range(maze.n_rows)]

    # Add the source cell to the open list
    src_cell = maze.grid[src[0]][src[1]]
    src_cell.g = 0
    src_cell.h = calculate_h_value(src[0], src[1], dest)
    src_cell.f = src_cell.g + src_cell.h
    open_list.append(src_cell)

    while open_list:
        # Get the cell with the lowest f value
        current_cell = min(open_list, key=lambda cell: cell.f)
        open_list.remove(current_cell)

        # Mark the current cell as closed
        closed_list[current_cell.row][current_cell.col] = True

        # Check if we have reached the destination
        if is_destination(current_cell.row, current_cell.col, dest):
            path = trace_path(maze, current_cell)
            print("Destination reached!")
            found_dest = True
            return path

        # Generate the 4 possible moves (up, down, left, right)
        for move in range(4):
            new_row = current_cell.row + (move == 0) - (move == 1)  # up/down
            new_col = current_cell.col + (move == 2) - (move == 3)  # left/right

            if (
                maze.is_valid_move(current_cell.row, current_cell.col, move)
                and not closed_list[new_row][new_col]
            ):
                neighbor_cell = maze.grid[new_row][new_col]
                tentative_g = current_cell.g + 1

                if tentative_g < neighbor_cell.g:
                    neighbor_cell.g = tentative_g
                    neighbor_cell.h = calculate_h_value(new_row, new_col, dest)
                    neighbor_cell.f = neighbor_cell.g + neighbor_cell.h
                    neighbor_cell.parent = current_cell

                    if neighbor_cell not in open_list:
                        open_list.append(neighbor_cell)

    if not found_dest:
        print("Failed to find the destination")
        return None


def draw_path(maze_img, path, cell_size=140, margin=40, color=(0, 0, 0), thickness=3):
    """Draw the path on the maze image.

    Args:
        maze_img: The maze image to draw on
        path: List of (row, col) tuples representing the path
        cell_size: Size of each cell in pixels
        margin: Margin around the maze in pixels
        color: Color of the path (BGR)
        thickness: Thickness of the path line
    """
    if path is None or len(path) == 0:
        return maze_img

    img = maze_img.copy()

    # Draw circles at each cell center
    for row, col in path:
        pixel_x = margin + col * cell_size + cell_size // 2
        pixel_y = margin + row * cell_size + cell_size // 2

        # bot cell in green, target cell in red, path cells in specified color
        if (row, col) == path[0]:  # bot cell
            cv.circle(img, (pixel_x, pixel_y), 15, (0, 255, 0), -1)
        elif (row, col) == path[-1]:  # target cell
            cv.circle(img, (pixel_x, pixel_y), 15, (0, 0, 255), -1)
        else:
            cv.circle(img, (pixel_x, pixel_y), 8, (0, 0, 0), -1)

    # Draw lines connecting the path
    for i in range(len(path) - 1):
        row1, col1 = path[i]
        row2, col2 = path[i + 1]

        pixel_x1 = margin + col1 * cell_size + cell_size // 2
        pixel_y1 = margin + row1 * cell_size + cell_size // 2
        pixel_x2 = margin + col2 * cell_size + cell_size // 2
        pixel_y2 = margin + row2 * cell_size + cell_size // 2

        cv.line(img, (pixel_x1, pixel_y1), (pixel_x2, pixel_y2), (0, 0, 0), thickness)

    return img


# main function to find path
def find_path(maze: Maze):
    start = (maze.bot_cell.row, maze.bot_cell.col)
    target = (maze.target_cell.row, maze.target_cell.col)

    # A* search to find path
    path = a_star_search(maze, start, target)
    return path


def test():
    # ---- testing
    image_path = "images/maze_obj.png"
    image_path = "images/maze_aruco1.png"

    result = build_maze_from_path(
        image_path=image_path,
        rows=3,
        cols=11,
        kernel_len=25,
        min_length=20,
        overlap_ratio=0.4,
        cell_size=140,
        margin=40,
        wall_thickness=4,
    )
    maze = result["maze"]

    # find path
    path = find_path(maze)

    # Draw the path on the maze image
    maze_img = result["grid_img"]
    if path:
        maze_img_with_path = draw_path(
            maze_img, path, cell_size=140, margin=40, color=(0, 0, 0)
        )
    else:
        maze_img_with_path = maze_img

    if DEBUG:
        cv.imshow("Maze Grid with Path", maze_img_with_path)
        # cv.imshow("image", cv.imread(image_path))
        cv.imshow("mask", result["mask"])
        cv.waitKey(0)
        cv.destroyAllWindows()


if __name__ == "__main__":
    test()
