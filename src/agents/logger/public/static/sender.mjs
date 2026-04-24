import { Agent } from "./agent.mjs"

export class Message {
    /**
     * @param {import("./agent.mjs").AgentMessage} body
     * @param {String} recipient
     */
    constructor(body, recipient) {
        this.body = body
        this.recipient = recipient
    }
}

export class Sender {
    /**
     * @param {Agent} agent
     * @param {HTMLElement} node
     */
    constructor(agent, node) {
        this.agent = agent
        this.node = node

        this.recipientType = "predefined"

        this.initListeners()
    }

    initListeners() {
        const radioOpts = this.node.querySelectorAll("#recipient-type input[type='radio']")
        radioOpts.forEach(/** @param {HTMLInputElement} opt */ opt => {
            opt.addEventListener("change", () => {
                if (opt.checked) {
                    this.setRecipientType(opt.value)
                }
            })
        })

        this.node.querySelector("#sender-send").addEventListener("click", () => this.send())
        // TODO: bookmark button
    }

    setRecipientType(recipientType, updateRadio = false) {
        this.recipientType = recipientType
        const recipient = this.node.querySelector("#recipient")
        Array.from(recipient.children).forEach(child => {
            const show = child.dataset.type === recipientType
            child.classList.toggle("show", show)
        })
        if (updateRadio) {
            this.node.querySelector(
                `#recipient-type input[type='radio', value='${recipientType}']`
            ).checked = true
        }
    }

    getRecipient() {
        const input = this.node.querySelector(`#recipient [data-type='${this.recipientType}']`)
        return input.value
    }

    getBody() {
        const body = this.node.querySelector("#sender-message").value
        try {
            const data = JSON.parse(body)
            return data
        } catch (e) {
            // TODO
            throw e
        }
    }

    getMessage() {
        return new Message(
            this.getBody(),
            this.getRecipient()
        )
    }

    loadMessage(message) {
        const recipient = this.node.querySelector("#recipient [data-type='manual']")
        recipient.value = message.recipient

        const body = this.node.querySelector("#sender-message")
        body.value = message.body

        this.setRecipientType("manual")
    }

    send() {
        const message = this.getMessage()
        this.agent.send(message.body, message.recipient)
    }
}
