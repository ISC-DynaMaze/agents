import { Agent } from "./agent.mjs"

class AngleSlider {
    /**
     * @param {HTMLElement} node 
     */
    constructor(node) {
        this.node = node

        /** @type {HTMLDivElement} */
        this.curLabel = this.node.querySelector(".current")
        /** @type {HTMLInputElement} */
        this.slider = this.node.querySelector("input[type='range']")

        this.listeners = []

        this.initListeners()
    }

    initListeners() {
        this.slider.addEventListener("change", () => {
            const value = +this.slider.value
            this.setValue(value)
            this.listeners.forEach(listener => listener(value))
        })
    }

    setValue(value, updateSlider = false) {
        this.curLabel.innerText = `${value}°`
        if (updateSlider) {
            this.slider.value = value
        }
    }

    onChange(listener) {
        this.listeners.push(listener)
    }
}

export class RobotCamera {
    /**
     * @param {Agent} agent
     * @param {HTMLElement} node
     */
    constructor(agent, node) {
        this.agent = agent
        this.node = node

        /** @type {HTMLImageElement} */
        this.image = this.node.querySelector("#image-display")
        this.takePictureBtn = this.node.querySelector("#take-pic")
        this.setHomeBtn = this.node.querySelector("#set-home")
        this.panSlider = new AngleSlider(this.node.querySelector(".pan"))
        this.tiltSlider = new AngleSlider(this.node.querySelector(".tilt"))

        this.initListeners()
    }

    initListeners() {
        this.takePictureBtn.addEventListener("click", () => this.takePicture())
        this.setHomeBtn.addEventListener("click", () => this.setAngles(0, 0))
        this.panSlider.onChange(pan => this.setAngles(pan, null))
        this.tiltSlider.onChange(tilt => this.setAngles(null, tilt))

        this.agent.on("bot-img", msg => {
            this.displayImage(msg.img)
        })

        this.agent.on("cam-status", msg => {
            this.panSlider.setValue(msg.status.pan)
            this.tiltSlider.setValue(msg.status.tilt)
        })

        // TODO: nudge buttons
    }

    displayImage(base64Img) {
        this.image.src = `data:image/png;base64,${base64Img}`
    }

    takePicture() {
        this.agent.send({
            type: "bot-cam-photo-req"
        }, "alberto-robot")
    }

    setAngles(panAngle = null, tiltAngle = null) {
        this.agent.send({
            type: "bot-pan-tilt-req",
            pan: panAngle,
            tilt: tiltAngle
        }, "alberto-robot")
    }
}