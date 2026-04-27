import logging
from typing import Any, Optional

import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode
from spade.agent import Agent


class RefereeAgent(Agent):
    def __init__(self, *args, mqtt_host: str, mqtt_port: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.mqtt_host: str = mqtt_host
        self.mqtt_port: int = mqtt_port
        self.logger = logging.getLogger("RefereeAgent")
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # type: ignore
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_disconnect = self.on_disconnect
        self.mqttc.on_message = self.on_message

    async def setup(self) -> None:
        self.mqttc.connect(self.mqtt_host, self.mqtt_port)
        self.mqttc.loop_start()
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
        pass
