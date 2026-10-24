![CI](https://github.com/Buie-Dev/home-server.flow-sensor/actions/workflows/ci.yml/badge.svg?branch=dev)

# home-server.flow-sensor

ESP32 MicroPython service that reads a flow sensor and publishes pulse data over MQTT.

## Why I built it

The flow sensor sends second-by-second pulse data to the MQTT broker. The irrigation-controller subscribes to this data and uses it to track how much water flows through each zone over time. The mobile app and web app show the live flow readings while irrigation is running.

## How it fits

This runs on a dedicated ESP32 wired to a flow sensor inline with the irrigation water supply. It publishes to the same Mosquitto MQTT broker that all other services use.

- [home-server.infra](https://github.com/Buie-Dev/home-server.infra) runs the Mosquitto MQTT broker this sensor publishes to
- [irrigation-controller](https://github.com/Buie-Dev/irrigation-controller) subscribes to `irrigation/flow` and converts pulses to litres
- [home-server.api](https://github.com/Buie-Dev/home-server.api) is the Flask REST API
- [home-server.web](https://github.com/Buie-Dev/home-server.web) and [home-server.mobile](https://github.com/Buie-Dev/home-server.mobile) display live flow data

## Stack

- MicroPython on ESP32 NodeMCU
- DIGITEN FL-608 G3/4" hall-effect flow sensor
- MQTT via umqtt.simple
- Bash scripts for flashing and uploading

## Running it locally

### Prerequisites

- Python 3.10+ with `esptool` and `mpremote` installed
- ESP32 NodeMCU connected via USB
- CP210x USB driver (Mac only, from Silicon Labs)

```bash
pip3 install esptool mpremote
```

### First time setup

1. Clone the repo

```bash
git clone https://github.com/Buie-Dev/home-server.flow-sensor.git
cd home-server.flow-sensor
```

2. Flash MicroPython firmware onto the ESP32

```bash
./flash.sh
```

3. Create `.env` from the example and fill in your WiFi and MQTT credentials

```bash
cp .env.example .env
```

4. Upload the sensor code to the ESP32

```bash
./upload.sh
```

This generates `config.py` from `.env`, uploads it along with `index.py` (as `main.py`), and the ESP32 starts publishing on reboot.

## Configuration

| Variable | Purpose |
|---|---|
| `WIFI_SSID` | WiFi network name |
| `WIFI_PASSWORD` | WiFi password |
| `MQTT_BROKER` | MQTT broker IP address |
| `MQTT_PORT` | MQTT broker port (1883) |
| `MQTT_USER` | MQTT username (blank if no auth) |
| `MQTT_PASSWORD` | MQTT password (blank if no auth) |
| `SENSOR_NAME` | Device name used as MQTT client ID and in health check responses |

## Tests

There are no automated tests. This is a hardware project that runs on bare-metal MicroPython. CI runs ShellCheck on the bash scripts.

To monitor the sensor output, connect to the serial console:

```bash
mpremote connect /dev/cu.SLAB_USBtoUART repl
```

## Wiring

| Wire | ESP32 Pin | Notes |
|---|---|---|
| Red (VCC) | VIN (5V) | 5V preferred |
| Black (GND) | GND | Common ground |
| Yellow (Signal) | GPIO 14 | Hall-effect pulse output, internal pull-up enabled |

An external 10k ohm pull-up resistor between signal and 3.3V is optional. Only add one if you get erratic pulse counts.

## MQTT topics

| Direction | Topic | Payload |
|---|---|---|
| Publish | `irrigation/flow` | `{ sensor, pulse_count, elapsed_s }` every 1 second |
| Subscribe | `healthcheck/request` | Any message triggers a health response |
| Publish | `healthcheck/response` | `{ device: "<sensor_name>" }` |

## Calibration

The FL-608 outputs roughly 330 pulses per litre (from the spec formula `F = 5.5 x Q` where Q is litres per minute). The irrigation-controller handles the conversion from pulses to litres. To verify the calibration, flow exactly 1 litre through the sensor and check the total pulse count.

## Troubleshooting

**Board not detected** — Hold BOOT, tap EN, release BOOT, then run the command. Try a different USB cable since many are charge-only. Install the CP210x driver if the port never appears.

**WiFi not connecting** — SSID and password are case-sensitive. The ESP32 only supports 2.4 GHz networks.

**MQTT not connecting** — Confirm the broker IP and that port 1883 is reachable. Set MQTT_USER and MQTT_PASSWORD if the broker requires auth.

**Zero pulse count** — Confirm the yellow wire is on GPIO 14 and VCC is connected. The sensor clicks faintly when water flows if powered.

## How I work on it

Changes start as specs in `docs/specs/`. Claude Code implements them on a branch and I review and merge every pull request.
