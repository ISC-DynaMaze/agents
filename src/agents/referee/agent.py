import json
import logging
from typing import Any, Optional

import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode
from spade.agent import Agent

from agents.referee.button_helper import (
    ButtonEvent,
    ButtonHandlerMixin,
    ButtonHelper,
    button_handler,
)
from agents.referee.gate import Gate, GateRole, GateTeam
from agents.referee.state import State


class RefereeAgent(Agent, ButtonHandlerMixin):
    TEAM1_COLOR = (0, 0, 255)
    TEAM2_COLOR = (255, 120, 0)
    START_COLOR = (0, 255, 0)
    END_COLOR = (255, 0, 0)
    ASSIGNING_COLOR = (255, 240, 100)
    IDLE_COLOR = (200, 200, 200)

    def __init__(self, *args, mqtt_host: str, mqtt_port: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.mqtt_host: str = mqtt_host
        self.mqtt_port: int = mqtt_port
        self.logger = logging.getLogger("RefereeAgent")
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # type: ignore
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_disconnect = self.on_disconnect
        self.mqttc.on_message = self.on_message

        self.state: State = State.IDLE
        self.gates: dict[str, Gate] = {}
        self.buttons: ButtonHelper = ButtonHelper()
        self.register_handlers(self.buttons)

    async def setup(self) -> None:
        self.mqttc.connect(self.mqtt_host, self.mqtt_port)
        self.mqttc.loop_start()
        self.mqttc.subscribe("+/status")
        self.mqttc.subscribe("+/button")
        self.mqttc.subscribe("+/ir")
        return await super().setup()

    def on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        connect_flags: mqtt.ConnectFlags,
        reason_code: ReasonCode,
        properties: Optional[Properties],
    ):
        self.logger.info("Connected to MQTT broker")

    def on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: mqtt.DisconnectFlags,
        reason_code: ReasonCode,
        properties: Optional[Properties],
    ):
        self.logger.info("Disconnected from MQTT broker")

    def on_message(self, client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage):
        address = message.topic.split("/")[0]
        if mqtt.topic_matches_sub("+/status", message.topic):
            self.on_status(address, message.payload)
        elif mqtt.topic_matches_sub("+/button", message.topic):
            self.on_button(address, bool(int(message.payload)))

    def set_led(self, address: str, color: tuple[int, int, int]):
        self.mqttc.publish(f"{address}/led", json.dumps(color))

    def on_status(self, address: str, status: bytes):
        match status:
            case b"connected":
                self.gates[address] = Gate(address)
                self.logger.info(f"Gate {address} connected")
                self.set_led(address, self.IDLE_COLOR)
            case b"disconnected":
                if address in self.gates:
                    self.gates.pop(address)
                self.logger.info(f"Gate {address} disconnected")

    def on_button(self, address: str, is_pressed: bool):
        self.logger.debug(f"{address} is now {'pressed' if is_pressed else 'released'}")
        self.buttons.update(address, is_pressed)

    @button_handler(ButtonEvent.CLICK, ButtonEvent.DOUBLE_CLICK, ButtonEvent.LONG_CLICK)  # type: ignore
    def on_team_assign(self, button_id: str, event: ButtonEvent) -> bool:
        if self.state != State.TEAM_ASSIGN:
            return False
        if button_id not in self.gates:
            return False
        if event == ButtonEvent.LONG_CLICK:
            self.state = State.ROLE_ASSIGN
            self.set_led(button_id, self.ASSIGNING_COLOR)
            return True
        gate: Gate = self.gates[button_id]
        gate.team = (
            GateTeam.TEAM2 if event == ButtonEvent.DOUBLE_CLICK else GateTeam.TEAM1
        )
        self.logger.info(f"Gate {button_id} assigned to team {gate.team}")
        self.set_led(
            button_id,
            self.TEAM2_COLOR if gate.team == GateTeam.TEAM2 else self.TEAM1_COLOR,
        )
        return True

    @button_handler(ButtonEvent.CLICK, ButtonEvent.DOUBLE_CLICK, ButtonEvent.LONG_CLICK)  # type: ignore
    def on_role_assign(self, button_id: str, event: ButtonEvent) -> bool:
        if self.state != State.ROLE_ASSIGN:
            return False
        if button_id not in self.gates:
            return False
        if event == ButtonEvent.LONG_CLICK:
            self.state = State.IDLE
            return True
        gate: Gate = self.gates[button_id]
        gate.role = GateRole.END if event == ButtonEvent.DOUBLE_CLICK else GateRole.START
        self.logger.info(f"Gate {button_id} assigned role {gate.role}")
        self.set_led(
            button_id,
            self.START_COLOR if gate.role == GateRole.START else self.END_COLOR,
        )
        return True

    @button_handler(ButtonEvent.LONG_CLICK)  # type: ignore
    def on_start_assign(self, button_id: str, event: ButtonEvent) -> bool:
        if self.state != State.IDLE:
            return False
        self.logger.info(f"Start assigning gate {button_id}")
        self.state = State.TEAM_ASSIGN
        self.set_led(button_id, self.ASSIGNING_COLOR)
        return True
