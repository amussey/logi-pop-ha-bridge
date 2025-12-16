import asyncio
import json
import time
from dataclasses import dataclass

from bleak import AdvertisementData, BleakClient, BLEDevice
from mqtt_client import MqttClient

LOGITECH_MFG_ID = 257
LOGI_DEVICE_NAME = "logi switch"
BUTTON_CHARACTERISTIC_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"


@dataclass
class LogiButton:
    device: BLEDevice
    mqtt_client: MqttClient
    last_event_counter: int = -1  # Initialize to -1 to indicate no events processed yet
    seen_nonces: set = None
    trigger_click_on_connect: bool = True

    def __post_init__(self):
        # Publish Home Assistant discovery config on initialization
        self.publish_ha_discovery_config()

    def publish_ha_discovery_config(self):
        """
        Publishes the configuration payload to Home Assistant's discovery topic.
        This makes the button appear as a device with a trigger.
        """
        discovery_payload = {
            "automation_type": "trigger",
            "topic": self.action_topic,
            "type": "button_short_press",  # We can use any of HA's built-in types
            "subtype": "button_1",
            "payload": "press",  # The message we'll send on the action topic
            "device": {
                "identifiers": [self.device_id],
                "name": self.name,
                "manufacturer": "Logitech (via Python Bridge)",
            },
        }
        # Convert dict to JSON string and publish
        payload_str = json.dumps(discovery_payload)
        print(f"Publishing MQTT Discovery config to: {self.config_topic}")

        # Retain ensures HA sees it after a restart
        self.mqtt_client.client.publish(self.config_topic, payload_str, retain=True)

    def notification_handler(self, sender, data: bytearray):
        """Handles decoded button click notifications from a bonded device."""
        if len(data) < 3:
            return

        click_type_byte = data[0]
        nonce = bytes(data[1:3])

        if self.seen_nonces is None:
            self.seen_nonces = set()
        if nonce in self.seen_nonces:
            return
        self.seen_nonces.add(nonce)

        click_type_str = "Unknown"
        if click_type_byte == 0x02:
            click_type_str = "Single Press"
        elif click_type_byte == 0x03:
            click_type_str = "Long Press"
        elif click_type_byte == 0x04:
            click_type_str = "Double Press"

        self._trigger_press(click_type_str)

    def _trigger_press(self, click_type: str):
        """Publishes an MQTT message indicating a button press event."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"[{timestamp}] {self.device_id}: {click_type} (published: {self.action_topic})"
        )
        self.mqtt_client.client.publish(self.action_topic, "press")

    async def listen(self):
        print(f"Listening for events from button: {self.device.address}")
        # Additional listening logic can be implemented here
        if self.trigger_click_on_connect:
            self._trigger_press("Connection Press")
        async with BleakClient(self.device) as client:
            try:
                if client.is_connected:
                    print(f"Connected to button: {self.address}")
                    if self.seen_nonces is None:
                        self.seen_nonces = set()
                    self.seen_nonces.clear()

                    await client.start_notify(
                        BUTTON_CHARACTERISTIC_UUID, self.notification_handler
                    )

                    while client.is_connected:
                        await asyncio.sleep(0.5)

            except Exception as e:
                print(f"Connection lost or failed: {e}")
            finally:
                print("Returning to scanning mode.")
                await asyncio.sleep(0.1)

    @property
    def address(self):
        return self.device.address

    @property
    def device_id(self):
        return f"logi_pop_switch_{self.address.replace(':', '').lower()}"

    @property
    def name(self):
        return f"Logi Pop Switch ({self.address.replace(':', '').lower()})"

    @property
    def action_topic(self):
        return f"homeassistant/device_automation/{self.device_id}/action"

    @property
    def config_topic(self):
        return f"homeassistant/device_automation/{self.device_id}/config"

    @classmethod
    def is_logi_button(cls, device: BLEDevice, advertisement_data: AdvertisementData):
        """
        Callback function that is called when a device is discovered or
        advertising data is received.
        """
        # Get the device name. Prefer the name in the advertisement data (local_name),
        # falling back to the cached device.name, or Unknown.
        device_name = advertisement_data.local_name or device.name or "Unknown"

        return (
            LOGI_DEVICE_NAME in device_name.lower()
            and LOGITECH_MFG_ID in advertisement_data.manufacturer_data
        )
