const OFFSETS = [
    [0, -1],
    [1, 0],
    [0, 1],
    [-1, 0],
]

function parseMaze(data) {
    const lines = data.trim().split("\n")
    const maze = {
        rows: (lines.length - 1) / 2,
        cols: (lines[0].length - 1) / 2,
        cells: [],
    }

    for (let row = 0; row < maze.rows; row++) {
        const mazeRow = []
        for (let col = 0; col < maze.cols; col++) {
            const x = col * 2 + 1
            const y = row * 2 + 1
            const walls = OFFSETS.map(([dx, dy]) => {
                return lines[y + dy][x + dx] === "#"
            })
            mazeRow.push({row: row, col: col, walls: walls})
        }
        maze.cells.push(mazeRow)
    }
    return maze
}

export const EXAMPLE_MAZE = parseMaze(`
#######################
#   #       #     #   #
# ##### #   # #   # # #
#       #     #   # # #
# #   # ####### #   # #
# #   # #     # #   # #
#######################
`)

export const EXAMPLE_PATH = [
    [ 1, 0],
    [ 0, 0],
    [ 0, 1],
    [ 1, 1],
    [ 2, 1],
    [ 3, 1],
    [ 3, 0],
    [ 4, 0],
    [ 5, 0],
    [ 5, 1],
    [ 6, 1],
    [ 6, 0],
    [ 7, 0],
    [ 8, 0],
    [ 8, 1],
    [ 8, 2],
    [ 9, 2],
    [ 9, 1],
    [ 9, 0],
    [10, 0],
    [10, 1],
    [10, 2],
]