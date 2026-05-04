from agents.controller.maze.grid import Cell


class Obstacle:
    def __init__(self):
        self.cells: list[Cell] = []  # list of cells occupied by the obstacle
        self.center = None
        self.corners = None
        self.color_range = [[(0, 0, 0), (0, 0, 0)]]

    def set_cell(self, cell):
        self.cells.append(cell)

    def set_corners(self, corners):
        self.corners = corners

    def set_center(self, center):
        self.center = center

    # find all the cells concerned by the obstacle
    def find_cells(self, maze):
        if self.corners is None:
            return

        for corner in self.corners:
            x, y = corner
            row, col = maze.pixel_to_cell(x, y)
            cell = maze.get_cell(row, col)
            if cell is not None and cell not in self.cells:
                self.set_cell(cell)


class greenObstacle(Obstacle):
    def __init__(self):
        super().__init__()
        self.color_range = [[(35, 50, 50), (85, 255, 255)]]

class yellowObstacle(Obstacle):
    def __init__(self):
        super().__init__()
        self.color_range = [[(20, 80, 80), (35, 255, 255)]]
