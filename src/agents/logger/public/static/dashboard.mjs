import { Agent } from "./agent.mjs";
import { RobotCamera } from "./bot_camera.mjs";
import { Logger } from "./logger.mjs";
import { Sender } from "./sender.mjs";

export class Dashboard {
    constructor() {
        // TODO: set host button
        this.agent = new Agent()
        this.sender = new Sender(this.agent, document.getElementById("sender"))
        this.robotCamera = new RobotCamera(this.agent, document.getElementById("bot-cam"))
        this.logger = new Logger(this.agent, document.getElementById("logger"))
    }
}