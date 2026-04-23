const HOST = "isc-coordinator.lan"
const Recipients = {
    ROBOT: `alberto-robot@${HOST}`,
    CONTROLLER: `alberto-ctrl@${HOST}`,
    CAMERA: `camera@${HOST}`,
    LOGGER: `logger@${HOST}`,
}

/** @type {WebSocket} */
var ws

function setHost() {
    const newHost = document.getElementById("xmpp-host").value
    const recipients = document.getElementById("recipients")
    Array.from(recipients.children).forEach(c => {
        const [name, host] = c.value.split("@")
        c.value = `${name}@${newHost}`
    })
}

function onWsMessage(event) {
    const msg = JSON.parse(event.data)
    switch (msg.type) {
        case "msg":
            logMessage(msg.msg)
            break
        case "bot-img":
            displayImage(msg.img)
            break
        case "cam-status":
            document.getElementById("current-pan").innerText = msg.status.pan.toString()
            document.getElementById("current-tilt").innerText = msg.status.tilt.toString()
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

function send(message, recipient) {
    if (typeof message !== "string") {
        message = JSON.stringify(message)
    }
    ws.send(JSON.stringify({
        "type": "send",
        "msg": message,
        "to": recipient
    }))
}

function sendMessage() {
    const message = document.getElementById("sender-message").value
    const recipient = document.getElementById("sender-recipient").value
    send(message, recipient)
}

function initRobot() {
    document.getElementById("take-pic").addEventListener("click", () => send({
        "type": "bot-cam-photo-req"
    }, Recipients.ROBOT))
    document.getElementById("set-home").addEventListener("click", () => send({
        "type": "bot-pan-tilt-req",
        "pan": 0,
        "tilt": 0,
    }, Recipients.ROBOT))
    document.getElementById("set-pan").addEventListener("click", () => send({
        "type": "bot-pan-tilt-req",
        "pan": document.getElementById("new-pan").value
    }, Recipients.ROBOT))
    document.getElementById("set-tilt").addEventListener("click", () => send({
        "type": "bot-pan-tilt-req",
        "tilt": document.getElementById("new-tilt").value
    }, Recipients.ROBOT))
}

window.addEventListener("load", () => {
    document.getElementById("set-xmpp-host").addEventListener("click", setHost)

    ws = new WebSocket("/ws")
    ws.addEventListener("message", onWsMessage)
    initSender()
    initRobot()
})