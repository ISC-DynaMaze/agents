/**
 * @typedef {object} AgentMessage
 * @property {String} type
 */

/**
 * @callback messageCallback
 * @param {AgentMessage} message
 */

export class Agent {
    constructor(host = "isc-coordinator.lan") {
        this.ws = new WebSocket("/ws")
        this.ws.addEventListener("message", event => this.onWSMessage(event))

        /** @type {Object.<string, messageCallback[]>} */
        this.listeners = {}

        this.hostKey = "dynamaze-host"
        this.hostInput = document.getElementById("xmpp-host")
        this.hostSetBtn = document.getElementById("set-xmpp-host")
        this.initListeners()
        this.host = host
        this.loadHost()
    }

    initListeners() {
        this.hostSetBtn.addEventListener("click", () => {
            this.host = this.hostInput.value
            localStorage.setItem(this.hostKey, this.host)
        })
    }

    loadHost() {
        const host = localStorage.getItem(this.hostKey)
        if (host) {
            this.host = host
            this.hostInput.value = host
        }
    }

    onWSMessage(event) {
        const msg = JSON.parse(event.data)
        const listeners = this.listeners[msg.type] ?? []
        listeners.forEach(listener => listener(msg))
    }

    /**
     * @param {String} type
     * @param {messageCallback} listener
     */
    on(type, listener) {
        if (!(type in this.listeners)) {
            this.listeners[type] = []
        }
        this.listeners[type].push(listener)
    }

    /**
     * @param {AgentMessage} message
     * @param {String} recipient
     */
    send(message, recipient) {
        if (!recipient.includes("@")) {
            recipient = `${recipient}@${this.host}`
        }
        this.ws.send(JSON.stringify({
            "type": "send",
            "msg": message,
            "to": recipient
        }))
    }

    /**
     * @param {String} message
     * @param {String} recipient
     */
    sendRaw(message, recipient) {
        if (!recipient.includes("@")) {
            recipient = `${recipient}@${this.host}`
        }
        this.ws.send(JSON.stringify({
            "type": "send-raw",
            "msg": message,
            "to": recipient
        }))
    }

    setHost(host) {
        this.host = host
    }
}