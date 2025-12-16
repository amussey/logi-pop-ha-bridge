from dataclasses import dataclass

from bleak import AdvertisementData, BLEDevice

LOGITECH_MFG_ID = 257
LOGI_DEVICE_NAME = "logi switch"


@dataclass
class LogiButton:
    device_name: str
    address: str
    last_event_counter: int = -1  # Initialize to -1 to indicate no events processed yet

    def get_event(self, advertisement_data: AdvertisementData) -> int | None:
        """
        Extracts the event counter from the advertisement data if available.

        Args:
            advertisement_data: The advertisement data received from the device.

        Returns:
            The event counter as an integer, or None if not available.
        """
        if LOGITECH_MFG_ID in advertisement_data.manufacturer_data:
            data = advertisement_data.manufacturer_data[LOGITECH_MFG_ID]
            if len(data) >= 12:

                event_counter = data[11]
                if event_counter != self.last_event_counter:
                    self.last_event_counter = event_counter
                    print(f"\n--- BUTTON PRESS DETECTED (Counter: {event_counter}) ---")
                    # print(f"Sending 'press' message to MQTT topic: {ACTION_TOPIC}")
                    print(f"Got a press event from device {self.device_id}")

        return None

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

    @classmethod
    def from_ble_device(cls, device: BLEDevice, advertisement_data: AdvertisementData):
        if not cls.is_logi_button(device, advertisement_data):
            raise ValueError("The provided device is not a Logi button.")

        return cls(
            device_name=advertisement_data.local_name or device.name or "Unknown",
            address=device.address,
        )
