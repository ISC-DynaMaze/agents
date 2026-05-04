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
        const y = row * 2 + 1
        for (let col = 0; col < maze.cols; col++) {
            const x = col * 2 + 1
            const walls = OFFSETS.map(([dx, dy]) => {
                return lines[y + dy][x + dx] === "#"
            })
            mazeRow.push({row: row, col: col, walls: walls})
        }
        maze.cells.push(mazeRow)
    }
    return maze
}

function parsePath(data) {
    const lines = data.trim().split("\n")
    const rows = (lines.length - 1) / 2
    const cols = (lines[0].length - 1) / 2

    let start = null
    let end = null

    // Find start and end points
    for (let row = 0; row < rows; row++) {
        const y = row * 2 + 1
        for (let col = 0; col < cols; col++) {
            const x = col * 2 + 1
            const char = lines[y][x]
            if (char === "S") {
                start = [col, row]
            } else if (char === "E") {
                end = [col, row]
            }
            if (start !== null && end !== null) {
                break
            }
        }
        if (start !== null && end !== null) {
            break
        }
    }
    if (start === null || end === null) {
        return []
    }

    // Visit neighbouring path cells
    const path = []
    const visited = []
    let [c, r] = start
    path.push(start)
    visited.push(r * cols + c)
    while (c !== end[0] || r !== end[1]) {
        const [x, y] = [c*2+1, r*2+1]
        let found = false
        for (let i = 0; i < OFFSETS.length; i++) {
            const [dx, dy] = OFFSETS[i]
            const [x2, y2] = [x + dx, y + dy]
            const [c2, r2] = [c + dx, r + dy]
            if (c2 < 0 || r2 < 0 || c2 >= cols || r2 >= rows) {
                continue
            }
            const id = r2 * cols + c2
            if (visited.includes(id)) {
                continue
            }
            const char = lines[y2][x2]
            if (char === "." || char === "E") {
                path.push([c2, r2])
                visited.push(id)
                c = c2
                r = r2
                found = true
                break
            }
        }
        if (!found) {
            return path
        }
    }
    path.push(end)
    return path
}

const MAZE_DATA = `
#######################
#..S#  .....#.....#...#
#.#####.#  .#.#  .#.#.#
#.......#  ...#  .#.#.#
# #   # ####### #.#.#.#
# #   # #     # #...#E#
#######################
`

export const EXAMPLE_MAZE = parseMaze(MAZE_DATA)
export const EXAMPLE_PATH = parsePath(MAZE_DATA)