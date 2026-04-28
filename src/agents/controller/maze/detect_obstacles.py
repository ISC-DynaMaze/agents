import numpy as np
import cv2

from agents.controller.maze.obstacles import yellowObstacle, redObstacle, greenObstacle

def get_image(image_path):
    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Error opening image: {image_path}")
    return img

# get a mask for given color
def get_obstacle_mask(image, obstacle):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # one color range (yellow and green)
    if len(obstacle.color_range) == 1:
        lower, upper = obstacle.color_range[0]
        mask = cv2.inRange(hsv, np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))
    # red that uses 2 color ranges
    else:
        lower_1, upper_1 = obstacle.color_range[0]
        lower_2, upper_2 = obstacle.color_range[1]
        mask_1 = cv2.inRange(hsv, np.array(lower_1, dtype=np.uint8), np.array(upper_1, dtype=np.uint8))
        mask_2 = cv2.inRange(hsv, np.array(lower_2, dtype=np.uint8), np.array(upper_2, dtype=np.uint8))
        mask = cv2.bitwise_or(mask_1, mask_2)

    # small cleanup to close gaps in obstacles
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    return mask 

# only keep object in the maze rectangle
def keep_only_maze_rect(mask, rect):
    x, y, w, h = rect
    rect_mask = np.zeros_like(mask, dtype=np.uint8)
    rect_mask[y:y + h, x:x + w] = 255
    return cv2.bitwise_and(mask, rect_mask)

# extract obstacle boxes from the mask
def extract_obstacle_boxes(mask, min_area=500):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        corners = get_obstacle_corners(contour)
        center_x = int(np.mean(corners[:, 0]))
        center_y = int(np.mean(corners[:, 1]))

        center = (center_x, center_y)
        boxes.append({
            "contour": contour,
            "corners": corners,
            "center": center,
            "area": area,
        })

    return boxes

## get corners of one object contour
def get_obstacle_corners(contour):
    epsilon = 0.02 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)

    # Keep true shape corners when we already have 4, otherwise force a 4-corner box.
    if len(approx) == 4:
        corners = approx.reshape(-1, 2)
    else:
        rect = cv2.minAreaRect(contour)
        corners = cv2.boxPoints(rect)

    return corners.astype(np.int32)

# create obstacle objects from detected blocks and add them to the maze
def build_obstacles_from_blocks(blocks, obstacle_cls, maze):
    detected_obstacles = []

    for block in blocks:
        obstacle = obstacle_cls()
        obstacle.set_corners(block["corners"])
        obstacle.set_center(block["center"])
        obstacle.find_cells(maze)
        detected_obstacles.append(obstacle)

    return detected_obstacles

# detect obstacles in the maze from the image, return dict of detected obstacles by color and their blocks
def detect_obstacles_in_maze(image, maze, rect, min_area=500):
    obstacle_classes = [redObstacle, greenObstacle, yellowObstacle]
    detected_by_color = {}
    blocks_by_color = {}

    # for each color, get mask, extract blocks and build obstacles from them
    for obstacle_cls in obstacle_classes:
        obstacle_probe = obstacle_cls()
        color_name = obstacle_cls.__name__

        # keep only objects in the maze rectangle
        color_mask = get_obstacle_mask(image, obstacle_probe)
        color_mask = keep_only_maze_rect(color_mask, rect)

        # extract blocks and build obstacles from them
        blocks = extract_obstacle_boxes(color_mask, min_area=min_area)
        obstacles = build_obstacles_from_blocks(blocks, obstacle_cls, maze)

        detected_by_color[color_name] = obstacles
        blocks_by_color[color_name] = blocks

    return detected_by_color, blocks_by_color

# clear maze obstacles and their references in cells
def clear_maze_obstacles(maze):
    maze.obstacles = []
    for row in maze.grid:
        for cell in row:
            cell.obstacles = []

# add detected obstacles to maze and link them to their cells
def add_detected_obstacles_to_maze(maze, detected_by_color):
    clear_maze_obstacles(maze)

    for obstacles in detected_by_color.values():
        for obstacle in obstacles:
            maze.add_obstacle(obstacle)


# draw detected obstacles on image for visualization with corners, centers and contours
def draw_detected_obstacles(image, blocks_by_color):
    highlighted = image.copy()

    # specific color for each type
    draw_colors = {
        "redObstacle": (0, 0, 255),
        "greenObstacle": (0, 255, 0),
        "yellowObstacle": (0, 255, 255),
    }

    for color_name, blocks in blocks_by_color.items():
        line_color = draw_colors.get(color_name, (255, 255, 255))

        for block in blocks:
            corners = block["corners"].reshape(-1, 1, 2)
            center = block["center"]

            cv2.polylines(highlighted, [corners], True, line_color, 2)

            for cx, cy in corners.reshape(-1, 2):
                cv2.circle(highlighted, (int(cx), int(cy)), 3, (255, 0, 0), -1)

            cv2.circle(highlighted, center, 3, (255, 255, 255), -1)

    return highlighted

# combine all obstacle blocks into one mask for visualization
def build_combined_obstacle_mask(image_shape, blocks_by_color):
    combined_mask = np.zeros(image_shape[:2], dtype=np.uint8)
    for blocks in blocks_by_color.values():
        for block in blocks:
            cv2.drawContours(combined_mask, [block["contour"]], -1, 255, thickness=cv2.FILLED)
    return combined_mask

# print summary of what was detected, kept in a function for debugging 
def print_detection_summary(detected_by_color, maze):
    for color_name, obstacles in detected_by_color.items():
        print(f"{color_name}: {len(obstacles)} obstacle(s)")
        for i, obstacle in enumerate(obstacles, start=1):
            cells = [(cell.row, cell.col) for cell in obstacle.cells]
            print(f"  #{i} center={obstacle.center} cells={cells}")

    print(f"Maze obstacle count: {len(maze.obstacles)}")

# main function
def find_obstacles(image, maze, min_area=500):
    if maze.rect is None:
        raise ValueError("Maze should be built before detecting obstacles")

    # create obstacle objects from detected blocks and add them to the maze
    detected_by_color, blocks_by_color = detect_obstacles_in_maze(
        image=image,
        maze=maze,
        rect=maze.rect,
        min_area=min_area,
    )
    add_detected_obstacles_to_maze(maze, detected_by_color)

    return {
        "detected_by_color": detected_by_color,
        "blocks_by_color": blocks_by_color,
        "maze": maze,
    }


def test():
    image_path = "images/maze_obs_1.jpg"
    image = get_image(image_path)

    # get maze from image
    result = build_maze_from_path(
                    image_path=image_path,
                    rows=3,
                    cols=11,
                    kernel_len=25,
                    min_length=30,
                    overlap_ratio=0.6,
                    cell_size=140,
                    margin=40,
                    wall_thickness=4,
                )
    maze = result["maze"]

    detection = find_obstacles(image=image, maze=maze, min_area=500)
    detected_by_color = detection["detected_by_color"]
    blocks_by_color = detection["blocks_by_color"]
    maze = detection["maze"]

    # visualization
    highlighted = draw_detected_obstacles(image, blocks_by_color)
    combined_mask = build_combined_obstacle_mask(image.shape, blocks_by_color)

    # summary
    #print_detection_summary(detected_by_color, maze)

    cv2.imshow("Highlighted Obstacles", highlighted)
    cv2.imshow("Combined Obstacle Mask", combined_mask)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test()