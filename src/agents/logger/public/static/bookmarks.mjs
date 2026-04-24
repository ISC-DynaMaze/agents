import { Agent } from "./agent.mjs"
import { Message } from "./sender.mjs"

export class Bookmark {
    /**
     * @param {String} name
     * @param {Message} message
     */
    constructor(name, message) {
        this.name = name
        this.message = message
    }
}

export class Bookmarks {
    /**
     * @param {Agent} agent
     * @param {HTMLElement} node
     */
    constructor(agent, node) {
        this.agent = agent
        this.node = node

        this.bookmarkID = 1

        this.template = document.getElementById("bookmark-template")
        this.list = this.node.querySelector("#saved-messages")
    }

    /**
     * @param {Message} message 
     */
    saveMessage(message) {
        const name = `Bookmark #${this.bookmarkID}`
        const bookmark = new Bookmark(name, message)
        this.bookmarkID++
        const node = this.makeNode(bookmark)
        this.list.appendChild(node)
    }

    /**
     * @param {Bookmark} bookmark
     * @returns {HTMLElement}
     */
    makeNode(bookmark) {
        /** @type {HTMLElement} */
        const node = this.template.cloneNode(true)
        node.removeAttribute("id")
        node.classList.remove("template")
        node.querySelector(".name").value = bookmark.name
        node.querySelector(".recipient").innerText = bookmark.message.recipient

        node.querySelector(".send").addEventListener("click", () => {
            this.agent.send(bookmark.message.body, bookmark.message.recipient)
        })
        node.querySelector(".delete").addEventListener("click", () => node.remove())
        return node
    }
}