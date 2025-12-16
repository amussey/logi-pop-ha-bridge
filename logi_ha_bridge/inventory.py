from bleak import AdvertisementData, BLEDevice
from button import LogiButton


class LogiButtonInventory:
    """
    Simple inventory to track known Logi buttons by their address.
    """

    def __init__(self):
        self._buttons: dict[str, LogiButton] = {}

    def get_or_add_button(
        self, device: BLEDevice, advertisement_data: AdvertisementData
    ) -> LogiButton:
        if device.address not in self._buttons:
            button = LogiButton.from_ble_device(device, advertisement_data)
            self._buttons[device.address] = button
        return self._buttons[device.address]

    def process_event(
        self, device: BLEDevice, advertisement_data: AdvertisementData
    ) -> int | None:
        button = self.get_or_add_button(device, advertisement_data)
        return button.get_event(advertisement_data)
