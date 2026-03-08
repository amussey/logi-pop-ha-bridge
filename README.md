# Logi POP HA Bridge

A Home Assistant bridge for **Logitech POP** BTLE smart buttons. The original Logitech POP hub has been discontinued and no longer functions - this project lets you keep using the buttons by listening for their BLE advertisements and publishing press events to Home Assistant via MQTT.

## How It Works

When you press a Logi POP button, it briefly wakes up and broadcasts BLE advertisements. This bridge runs a persistent BLE scanner that detects those advertisements and immediately fires an MQTT message to Home Assistant. Each button is automatically registered via [MQTT Discovery](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery), so it appears as a device trigger you can use in automations - no manual YAML configuration needed.

### Architecture

```
┌──────────────┐      BLE advert      ┌──────────────────┐      MQTT       ┌─────────────────┐
│  Logi POP    │  ─────────────────>  │  logi-pop-ha-    │  ────────────>  │  Home Assistant │
│  Button(s)   │                      │  bridge          │                 │                 │
└──────────────┘                      └──────────────────┘                 └─────────────────┘
                                        persistent scan                     MQTT Discovery
                                        no GATT connection                  device triggers
```

The bridge uses a **purely advertisement-based** detection model:

1. A persistent `BleakScanner` runs continuously, listening for BLE advertisements.
2. When a Logi POP button advertisement is detected (identified by device name and Logitech manufacturer ID `0x0101`), a press event is published to MQTT immediately.
3. A per-button cooldown (default: 3 seconds) prevents duplicate triggers from repeated advertisements for the same physical press.
4. No GATT connections are made, so the BLE adapter is never occupied - multiple buttons pressed within seconds of each other are all reliably detected.

## Design Tradeoffs

### Advertisement-only detection vs. GATT connections

The Logi POP buttons support a GATT characteristic (`0000fff4-0000-1000-8000-00805f9b34fb`) that can report the specific click type (single press, double press, long press) via notifications after a BLE connection is established. However, there is a significant tradeoff:

| | Advertisement-only (current) | GATT connection |
|---|---|---|
| **Multi-button reliability** | Excellent - scanner is never blocked | Poor - connecting to one button blocks scanning for others |
| **Latency** | Sub-second (fires on first advertisement) | 2-10 seconds (connect + subscribe + wait) |
| **Click type differentiation** | No - all presses reported as "Press" | Yes - Single, Double, Long Press |
| **Bonding required** | No | Yes (BlueZ pairing) |
| **Adapter availability** | Always free | Locked during connection |

**The current design prioritizes reliability and multi-button support over click type differentiation.** When multiple buttons are on the same desk, catching every press is more important than knowing whether it was a single or double click. In testing, using GATT connections caused the scanner to miss 80-90% of button presses from other buttons while one connection was active.

### Cooldown tuning

The 3-second cooldown was determined empirically:

- **Too short (≤2s):** Buttons re-advertise for ~1-2 seconds after a press, causing duplicate triggers.
- **Too long (≥5s):** Presses spaced 4 seconds apart on the same button get dropped.
- **3 seconds:** Reliably deduplicates re-advertisements while catching presses spaced ≥4 seconds apart on the same button. Different buttons can be pressed as fast as you can physically press them.

## Installation

### HACS (Home Assistant Community Store)

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations** (or **Automation** if available).
3. Click the three-dot menu (⋮) in the top-right corner and select **Custom repositories**.
4. Add the repository URL:
   ```
   https://github.com/amussey/logi-pop-ha-bridge
   ```
   Set the category to **Integration**.
5. Click **Add**, then find **Logi POP Switch Bridge** in the HACS store and click **Download**.
6. Restart Home Assistant.

### Home Assistant Add-on (manual)

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**.
2. Click the three-dot menu (⋮) and select **Repositories**.
3. Add this repository URL:
   ```
   https://github.com/amussey/logi-pop-ha-bridge
   ```
4. Find **Logi Pop Switch Bridge** in the list and click **Install**.
5. Configure the add-on (see [Configuration](#configuration) below).
6. Start the add-on.

### Docker

```bash
docker compose up -d
```

Create a `.env` file with your MQTT credentials:

```env
MQTT_BROKER_ADDRESS=192.168.1.x
MQTT_PORT=1883
MQTT_USERNAME=your_user
MQTT_PASSWORD=your_password
```

### Local (development)

```bash
pip install -e .
python3 logi_ha_bridge/runner.py
```

Requires a `.env` file or exported environment variables for MQTT configuration.

## Configuration

| Variable | Description | Default |
|---|---|---|
| `MQTT_BROKER_ADDRESS` | MQTT broker hostname or IP | `core-mosquitto` |
| `MQTT_PORT` | MQTT broker port | `1883` |
| `MQTT_USERNAME` | MQTT username | - |
| `MQTT_PASSWORD` | MQTT password | - |

When running as a Home Assistant add-on, these are configured through the add-on's configuration UI:

```yaml
mqtt_broker:
  address: "core-mosquitto"
  port: 1883
  username: "your_user"
  password: "your_password"
```

## Usage

Once running, the bridge automatically:

1. Scans for Logi POP button advertisements.
2. Publishes an MQTT Discovery config for each button it finds (retained, so HA remembers them across restarts).
3. Publishes a press event to `homeassistant/device_automation/<device_id>/action` each time a button is pressed.

In Home Assistant, your buttons will appear as device triggers that you can use in automations:

1. Go to **Settings → Automations & Scenes → Create Automation**.
2. Add a **Device** trigger.
3. Select your Logi POP Switch from the device list.
4. Choose **Button 1 short press** as the trigger.
5. Add your desired actions.
