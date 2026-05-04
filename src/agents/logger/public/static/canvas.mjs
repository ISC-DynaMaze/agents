export class Canvas {
    /**
     * @param {HTMLCanvasElement} node
     */
    constructor(node, aspect = 1) {
        this.canvas = node
        this.ctx = this.canvas.getContext("2d")
        this.margin = 10
        this.aspect = aspect

        window.addEventListener("resize", () => this.resize())
    }

    resize() {
        const parent = this.canvas.parentElement
        this.canvas.width = parent.clientWidth
        this.canvas.height = parent.clientWidth / this.aspect
    }

    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height)
    }

    /**
     * @param {[number, number]} pos
     * @returns
     */
    toViewport(pos) {
        return [
            pos[0] + this.margin,
            pos[1] + this.margin,
        ]
    }

    /**
     * @param {[number, number]} pos1
     * @param {[number, number]} pos2
     */
    drawLine(pos1, pos2) {
        const [x1, y1] = this.toViewport(pos1)
        const [x2, y2] = this.toViewport(pos2)
        this.ctx.beginPath()
        this.ctx.moveTo(x1, y1)
        this.ctx.lineTo(x2, y2)
        this.ctx.stroke()
    }

    fillCircle(pos, radius) {
        const [x, y] = this.toViewport(pos)
        this.ctx.beginPath()
        this.ctx.arc(x, y, radius, 0, Math.PI * 2)
        this.ctx.fill()
    }

    setColor(color) {
        this.ctx.strokeStyle = color
        this.ctx.fillStyle = color
    }

    setWidth(width) {
        this.ctx.lineWidth = width
    }
}