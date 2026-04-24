import { EditorView, basicSetup } from "https://esm.sh/codemirror"
import { keymap } from "https://esm.sh/@codemirror/view"
import { json, jsonParseLinter } from "https://esm.sh/@codemirror/lang-json"
import { linter, lintGutter } from "https://esm.sh/@codemirror/lint"
import { indentWithTab } from "https://esm.sh/@codemirror/commands"
import { tomorrow } from "https://esm.sh/thememirror"

import { Agent } from "./agent.mjs"

const customMessageLinter = linter(view => {
    let diagnostics = []
    try {
        const obj = JSON.parse(view.state.doc.toString())
        if (!("type" in obj)) {
            diagnostics.push({
                from: 0,
                to: view.state.doc.length,
                severity: "error",
                message: "Missing required field: 'type'"
            })
        }
    } catch (e) { }
    return diagnostics
})

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

        this.editorNode = this.node.querySelector("#sender-message")
        this.editor = new EditorView({
            doc: '{\n  "type": ""\n}',
            extensions: [
                basicSetup,
                json(),
                linter(jsonParseLinter()),
                customMessageLinter,
                lintGutter(),
                keymap.of([indentWithTab]),
                tomorrow
            ],
            parent: this.editorNode
        })

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
        const body = this.editor.state.doc.toString()
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
