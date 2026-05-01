export class Maze {
    /**
     * @param {Agent} agent
     * @param {HTMLElement} node
     */
    constructor(agent, node) {
        this.agent = agent
        this.node = node

        this.image = this.node.querySelector("#maze-display")

        this.initListeners()
    }

    initListeners() {
        this.agent.on("maze-img", msg => {
            this.displayImage(msg.img)
        })
    }

    displayImage(base64Img) {
        this.image.src = `data:image/png;base64,${base64Img}`
    }
}
