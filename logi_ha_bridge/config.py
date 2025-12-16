import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class MqttConfig:
    broker_address: str
    port: int
    username: str
    password: str


@dataclass
class Config:
    mqtt: MqttConfig

    @classmethod
    def load(cls):
        load_dotenv()

        return cls(
            mqtt=MqttConfig(
                broker_address=os.environ.get("MQTT_BROKER_ADDRESS"),
                port=int(os.environ.get("MQTT_PORT", 1883)),
                username=os.environ.get("MQTT_USERNAME"),
                password=os.environ.get("MQTT_PASSWORD"),
            )
        )
