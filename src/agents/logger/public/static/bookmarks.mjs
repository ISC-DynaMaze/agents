import { Agent } from "./agent.mjs"
import { Message } from "./sender.mjs"

export class Bookmark {
    /**
     * @param {String} name
     * @param {Message} message
     */
    constructor(name, message, id = undefined) {
        if (id !== undefined) {
            this.id = id
        }
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

        this.dbName = "DynaMaze-Logger"
        this.storeName = "bookmarks"
        this.dbVersion = 1
        this.loadBookmarks()
    }

    /**
     * @returns {Promise<IDBDatabase>}
     */
    openDB() {
        return new Promise((resolve, reject) => {
            const dbRequest = indexedDB.open(this.dbName, this.dbVersion)
            dbRequest.onupgradeneeded = event => {
                /** @type {IDBDatabase} */
                const db = event.target.result

                if (!db.objectStoreNames.contains(this.storeName)) {
                    db.createObjectStore(this.storeName, {
                        keyPath: "id",
                        autoIncrement: true
                    })
                }
            }

            dbRequest.onsuccess = event => {
                resolve(event.target.result)
            }

            dbRequest.onerror = e => {
                console.error("Error opening IndexedDB")
                reject(e.target.error)
            }
        })
    }

    async loadBookmarks() {
        const db = await this.openDB()
        const store = db
            .transaction(this.storeName, "readonly")
            .objectStore(this.storeName)

        const req = store.getAll()
        req.onsuccess = event => {
            const data = event.target.result
            data.forEach(bm => {
                const node = this.makeNode(bm)
                this.list.appendChild(node)
            })
        }
    }

    /**
     * @param {Bookmark} bookmark
     */
    async saveBookmarkToDB(bookmark) {
        const db = await this.openDB()
        const store = db
            .transaction(this.storeName, "readwrite")
            .objectStore(this.storeName)

        const req = store.put(bookmark)
        req.onsuccess = () => {
            bookmark.id = req.result
        }
    }

    /**
     * @param {Bookmark} bookmark
     */
    async removeBookmarkFromDB(bookmark) {
        const db = await this.openDB()
        const store = db
            .transaction(this.storeName, "readwrite")
            .objectStore(this.storeName)

        const req = store.delete(bookmark.id)
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
        this.saveBookmarkToDB(bookmark)
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
        const name = node.querySelector(".name")
        name.value = bookmark.name
        name.addEventListener("change", () => {
            bookmark.name = name.value
            this.saveBookmarkToDB(bookmark)
        })
        node.querySelector(".recipient").innerText = bookmark.message.recipient

        node.querySelector(".send").addEventListener("click", () => {
            this.agent.send(bookmark.message.body, bookmark.message.recipient)
        })
        node.querySelector(".delete").addEventListener("click", () => {
            node.remove()
            this.removeBookmarkFromDB(bookmark)
        })
        return node
    }
}