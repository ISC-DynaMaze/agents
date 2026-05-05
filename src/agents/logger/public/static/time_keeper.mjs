import { Agent } from "./agent.mjs"

const COUNTDOWN_MESSAGES = [
    "3", "2", "1", "Go !!!"
]

const RESULT_TIME_REGEX = new RegExp(/^The race is finished! Your race time is: (.*)s$/)

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
    }

    triggerPenalty() {
        this.agent.send({
            type: "penalty",
            duration: 5
        }, "alberto-robot")
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

    setCountdown(msg) {
        if (msg === COUNTDOWN_MESSAGES[COUNTDOWN_MESSAGES.length - 1]) {
            this.startTimer()
            // TODO: Start the robot
        }
        // TODO: show countdown
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