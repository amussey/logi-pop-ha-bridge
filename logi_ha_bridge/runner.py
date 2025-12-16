# logi_ha_bridge.py

import asyncio

from bleak import AdvertisementData, BleakScanner, BLEDevice
from button import LogiButton, LogiButtonInventory
from config import Config
from mqtt_client import MqttClient

# --- State Management ---
logi_button_inventory = LogiButtonInventory()
config = Config.load()


def on_advertisement(device: BLEDevice, advertisement_data: AdvertisementData):
    """
    Listens for a new event from the switch and publishes an MQTT message.
    """
    global logi_button_inventory

    if LogiButton.is_logi_button(device, advertisement_data):
        logi_button_inventory.process_event(device, advertisement_data)

        # mqtt_client.publish(ACTION_TOPIC, "press")


async def main():
    """The main function that starts the BLE scanner."""
    print("=" * 80)
    print("Starting Logi HA Bridge!")
    print("-" * 80)

    mqtt_client = MqttClient(config)
    mqtt_client.start()

    print("Starting Logi Switch listener...")
    scanner = BleakScanner(detection_callback=on_advertisement)
    await scanner.start()

    try:
        while True:
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("\nStopping scanner...")
        await scanner.stop()
        mqtt_client.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program stopped.")
