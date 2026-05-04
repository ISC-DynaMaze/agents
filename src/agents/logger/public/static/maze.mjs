import { Canvas } from "./canvas.mjs"
import { EXAMPLE_MAZE, EXAMPLE_PATH } from "./example_maze.mjs"

const WALLS = [
    "top", "right", "bottom", "left"
]

const OFFSETS = [
    [[0, 0], [1, 0]],
    [[1, 0], [1, 1]],
    [[0, 1], [1, 1]],
    [[0, 0], [0, 1]],
]

/**
 * @typedef {Object} MazeDataCell
 * @property {number} row
 * @property {number} cell
 * @property {[boolean, boolean, boolean, boolean]} walls
 */

/**
 * @typedef {Object} MazeData
 * @property {number} rows
 * @property {number} cols
 * @property {MazeDataCell[][]} cells
 */

/**
 * @typedef {[number, number][]} PathData
 */

class AbstractMaze extends Canvas {
    constructor(node) {
        super(node, 3)
        this.cellSize = 10
        /** @type {MazeData?} */
        this.maze = null
        /** @type {PathData?} */
        this.path = null
        this.resize()
    }

    resize() {
        super.resize()
        if (this.maze !== null) {
            this.redraw()
        }
    }

    toViewport(pos) {
        return super.toViewport([
            pos[0] * this.cellSize,
            pos[1] * this.cellSize,
        ])
    }

    /**
     * @param {MazeData} maze
     */
    setMaze(maze) {
        this.maze = maze
        this.redraw()
    }

    /**
     * @param {PathData} path
     */
    setPath(path) {
        this.path = path
        this.redraw()
    }

    redraw() {
        this.clear()

        if (this.maze === null) {
            return
        }

        const availableWidth = this.canvas.width - (this.margin * 2)
        this.cellSize = availableWidth / this.maze.cols

        const maze = this.maze
        this.setColor("red")
        this.setWidth(2)
        for (let y = 0; y < maze.rows; y++) {
            for (let x = 0; x < maze.cols; x++) {
                for (let i = 0; i < WALLS.length; i++) {
                    if (maze.cells[y][x].walls[i]) {
                        const [[dx1, dy1], [dx2, dy2]] = OFFSETS[i]
                        const x1 = x + dx1
                        const y1 = y + dy1
                        const x2 = x + dx2
                        const y2 = y + dy2
                        this.drawLine([x1, y1], [x2, y2])
                    }
                }
            }
        }

        if (this.path === null) {
            return
        }

        this.setColor("black")
        for (let i = 0; i < this.path.length - 1; i++) {
            const [x1, y1] = this.path[i]
            const [x2, y2] = this.path[i+1]
            this.drawLine([x1 + 0.5, y1 + 0.5], [x2 + 0.5, y2 + 0.5])
        }

        const [sx, sy] = this.path[0]
        const [ex, ey] = this.path[this.path.length - 1]
        this.setColor("#00ff00")
        this.fillCircle([sx + 0.5, sy + 0.5], this.cellSize * 0.2)
        this.setColor("#ff0000")
        this.fillCircle([ex + 0.5, ey + 0.5], this.cellSize * 0.2)
    }
}


export class Maze {
    /**
     * @param {Agent} agent
     * @param {HTMLElement} node
     */
    constructor(agent, node) {
        this.agent = agent
        this.node = node

        /** @type {HTMLImageElement} */
        this.image = this.node.querySelector("#maze-display")
        this.abstract = new AbstractMaze(this.node.querySelector("#abstract-maze"))

        this.initListeners()
        this.abstract.setMaze(EXAMPLE_MAZE)
        this.abstract.setPath(EXAMPLE_PATH)
    }

    initListeners() {
        this.agent.on("maze-img", msg => {
            this.displayImage(msg.img)
        })
        this.agent.on("maze", msg => {
            this.abstract.setMaze(msg.maze)
        })
        this.agent.on("path", msg => {
            const path = msg.path.map(([y, x]) => [x, y])
            this.abstract.setPath(path)
        })
    }

    displayImage(base64Img) {
        this.image.src = `data:image/png;base64,${base64Img}`
    }
}
