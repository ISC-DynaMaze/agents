import { Agent } from "./agent.mjs"

const COUNTDOWN_MESSAGES = [
    "3", "2", "1", "Go !!!"
]

const RESULT_TIME_REGEX = new RegExp(/^The race is finished! Your race time is: (.*)s$/)

const PENALTY_DURATION = 5000

/**
 * @enum {string}
 */
const Light = {
    OFF: "off",
    RED: "red",
    AMBER: "amber",
    GREEN: "green",
}

export class TimeKeeper {
    /**
     * @param {Agent} agent
     * @param {HTMLElement} node
     */
    constructor(agent, node) {
        this.agent = agent
        this.node = node

        this.startBtn = this.node.querySelector("#start-sess-btn")
        this.readyBtn = this.node.querySelector("#ready-btn")
        this.penaltyBtn = this.node.querySelector("#penalty-btn")

        this.countdown = this.node.querySelector(".countdown")
        this.light1 = this.countdown.querySelector(".light[data-idx='1']")
        this.light2 = this.countdown.querySelector(".light[data-idx='2']")
        this.light3 = this.countdown.querySelector(".light[data-idx='3']")

        this.timeDisplay = this.node.querySelector(".time")
        this.minSpan = this.timeDisplay.querySelector(".min")
        this.secSpan = this.timeDisplay.querySelector(".sec")
        this.msSpan = this.timeDisplay.querySelector(".ms")

        this.timerInterval = null
        this.startTime = 0

        this.initListeners()
    }

    initListeners() {
        this.startBtn.addEventListener("click", () => this.startSession())
        this.readyBtn.addEventListener("click", () => this.markReady())
        this.penaltyBtn.addEventListener("click", () => this.triggerPenalty())

        this.agent.on("raw-msg", msg => this.onRawMsg(msg))
    }

    sendTimeKeeper(message) {
        this.agent.sendRaw(message, "timekeeper")
    }

    startSession() {
        this.sendTimeKeeper("Hello TimeKeeper ! Please initialise a race.")
    }

    markReady() {
        this.sendTimeKeeper("I'm ready to race !")
        this.setCountdownLights(Light.RED, Light.RED, Light.RED)
    }

    triggerPenalty() {
        this.agent.send({
            type: "penalty",
            duration: PENALTY_DURATION / 1000
        }, "alberto-robot")
        this.timeDisplay.animate([
            { color: "red" },
            { color: "black" }
        ], {
            duration: PENALTY_DURATION,
            easing: "linear",
            fill: "both"
        })
    }

    /**
     * @typedef {object} RawMessage
     * @property {"raw-msg"} type
     * @property {String} msg
     * @property {String} sender
     */
    /**
     * @param {RawMessage} msg 
     */
    onRawMsg(msg) {
        if (COUNTDOWN_MESSAGES.includes(msg.msg)) {
            this.setCountdown(msg.msg)
        } else if (RESULT_TIME_REGEX.test(msg.msg)) {
            const match = msg.msg.match(RESULT_TIME_REGEX)
            const timeSec = +match[1]
            const timeMs = timeSec * 1000
            this.setFinalTime(timeMs)
        }
    }

    /**
     * @param {Light} col1
     * @param {Light} col2
     * @param {Light} col3
     */
    setCountdownLights(col1, col2, col3) {
        this.light1.dataset.color = col1
        this.light2.dataset.color = col2
        this.light3.dataset.color = col3
    }

    setCountdown(msg) {
        if (msg === COUNTDOWN_MESSAGES[COUNTDOWN_MESSAGES.length - 1]) {
            this.setCountdownLights(Light.GREEN, Light.GREEN, Light.GREEN)
            this.startTimer()
            setTimeout(() => {
                this.countdown.classList.remove("show")
                this.timeDisplay.classList.add("show")
            }, 1000)
            // TODO: Start the robot
        } else {
            const n = +msg
            this.setCountdownLights(
                Light.AMBER,
                n <= 2 ? Light.AMBER : Light.OFF,
                n <= 1 ? Light.AMBER : Light.OFF,
            )
        }
    }

    startTimer() {
        this.startTime = new Date().valueOf()
        this.timerInterval = setInterval(() => this.updateTimer(), 10)
    }

    setFinalTime(time) {
        clearInterval(this.timerInterval)
        this.setTime(time)
    }

    setTime(time) {
        const min = Math.floor(time / 60_000)
        const sec = Math.floor(time / 1000) % 60
        const ms = Math.round(time % 1000)
        this.minSpan.innerText = min.toString().padStart(2, "0")
        this.secSpan.innerText = sec.toString().padStart(2, "0")
        this.msSpan.innerText = ms.toString().padStart(3, "0")
    }

    updateTimer() {
        const now = new Date().valueOf()
        const delta = now - this.startTime
        this.setTime(delta)
    }
}