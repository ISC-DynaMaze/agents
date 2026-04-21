/** @type {WebSocket} */
var ws

function onWsMessage(event) {
    const msg = JSON.parse(event.data)
    switch (msg.type) {
        case "msg":
            logMessage(msg.msg)
            break
        case "bot-img":
            displayImage(msg.img)
            break
    }
}

function logMessage(msg) {
    const list = document.querySelector("#receiver .messages")
    const div = document.createElement("div")
    div.classList.add("message")
    div.innerText = JSON.stringify(msg)
    list.appendChild(div)
}

function displayImage(img) {
    /** @type {HTMLImageElement} */
    const node = document.getElementById("image-display")
    node.src = `data:image/png;base64,${img}`
}

function initSender() {
    document.getElementById("sender-send").addEventListener("click", sendMessage)
}

function sendMessage() {
    const message = document.getElementById("sender-message").value
    const recipient = document.getElementById("sender-recipient").value
    ws.send(JSON.stringify({
        "type": "send",
        "msg": message,
        "to": recipient
    }))
}

window.addEventListener("load", () => {
    ws = new WebSocket("/ws")
    ws.addEventListener("message", onWsMessage)
    initSender()
})