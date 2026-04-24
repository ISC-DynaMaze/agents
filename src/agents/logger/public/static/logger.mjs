import { Agent } from "./agent.mjs"

/**
 * @readonly
 * @enum {string}
 */
export const LogType = {
    ERROR: "error",
    WARNING: "warning",
    INFO: "info",
    DEBUG: "debug",
}

export class Logger {
    /**
     * @param {Agent} agent
     * @param {HTMLElement} node
     */
    constructor(agent, node) {
        this.agent = agent
        this.node = node

        /** @type {HTMLTableElement} */
        this.table = this.node.querySelector("#messages")

        this.initListeners()
    }

    initListeners() {
        this.agent.on("msg", msg => this.log(msg.log_type, msg.msg))
        // TODO: clear button
    }

    static getTimestamp() {
        const date = new Date()
        const hours = date.getHours().toString().padStart(2, "0")
        const minutes = date.getMinutes().toString().padStart(2, "0")
        const seconds = date.getSeconds().toString().padStart(2, "0")
        return `${hours}:${minutes}:${seconds}`
    }

    /**
     * @param {LogType} logType
     * @param {String} msg
     */
    log(logType, msg) {
        const row = this.table.insertRow()
        row.dataset.type = logType
        row.insertCell().innerText = Logger.getTimestamp()
        row.insertCell().innerText = logType.toUpperCase()
        row.insertCell().innerText = msg
    }

    clear() {
        this.table.innerHTML = ""
    }
}