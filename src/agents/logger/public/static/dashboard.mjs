import { Agent } from "./agent.mjs";
import { Bookmarks } from "./bookmarks.mjs";
import { RobotCamera } from "./bot_camera.mjs";
import { Logger } from "./logger.mjs";
import { Maze } from "./maze.mjs";
import { Sender } from "./sender.mjs";
import { TimeKeeper } from "./time_keeper.mjs";

export class Dashboard {
    constructor() {
        this.agent = new Agent()
        this.timeKeeper = new TimeKeeper(this.agent, document.getElementById("time-keeper"))
        this.sender = new Sender(this.agent, document.getElementById("sender"))
        this.bookmarks = new Bookmarks(this.agent, document.getElementById("saved"))
        this.robotCamera = new RobotCamera(this.agent, document.getElementById("bot-cam"))
        this.logger = new Logger(this.agent, document.getElementById("logger"))
        this.maze = new Maze(this.agent, document.getElementById("maze"))

        this.initListeners()
    }

    initListeners() {
        const saveBtn = document.getElementById("sender-save")
        saveBtn.addEventListener("click", () => {
            const message = this.sender.getMessage()
            this.bookmarks.saveMessage(message)
        })
    }
}