# CLAUDE.md

## What this repo is

MicroPython service for an ESP32 that reads a DIGITEN FL-608 hall-effect flow sensor and publishes pulse counts over MQTT. The irrigation-controller subscribes to this data and uses it to track water flow over time. The mobile app and web app display the live flow readings.

## Related repos

- [home-server.infra](https://github.com/Buie-Dev/home-server.infra) — Docker Compose infrastructure, runs the Mosquitto MQTT broker this sensor publishes to
- [irrigation-controller](https://github.com/Buie-Dev/irrigation-controller) — Raspberry Pi service that subscribes to `irrigation/flow` and converts pulses to litres
- [home-server.api](https://github.com/Buie-Dev/home-server.api) — Flask REST API
- [home-server.web](https://github.com/Buie-Dev/home-server.web) — React web app
- [home-server.mobile](https://github.com/Buie-Dev/home-server.mobile) — React Native mobile app

## Stack

- MicroPython on ESP32 NodeMCU
- DIGITEN FL-608 G3/4" hall-effect flow sensor
- MQTT via umqtt.simple
- Bash shell scripts for flashing and uploading

## Commands

```bash
./flash.sh          # Erase ESP32 and flash MicroPython firmware
./upload.sh         # Generate config.py from .env and upload to ESP32
./check_port.sh     # Find the ESP32 serial port
```

## File layout

```
index.py            # Main MicroPython script (uploaded as main.py to the ESP32)
upload.sh           # Generates config.py from .env, uploads index.py + config.py
flash.sh            # Erases flash and writes MicroPython firmware
check_port.sh       # Finds the USB serial port for the ESP32
.env                # WiFi and MQTT credentials (gitignored)
.env.example        # Template for .env
config.py           # Auto-generated from .env by upload.sh (gitignored)
```

## MQTT topics

| Direction | Topic | Payload |
|---|---|---|
| Publish | `irrigation/flow` | `{ sensor, pulse_count, elapsed_s }` every 1 second |
| Subscribe | `healthcheck/request` | Any message triggers a health response |
| Publish | `healthcheck/response` | `{ device: SENSOR_NAME }` |

## How the sensor works

The FL-608 outputs one electrical pulse per rotation of its internal turbine. The ESP32 counts these pulses via a GPIO interrupt. Every second, the script publishes the pulse count and resets it. The irrigation-controller converts pulses to litres using a calibration factor of 330 pulses per litre.

## Standards

- Two long-lived branches: `main` (stable) and `dev` (ongoing work)
- Spec branches named `spec/NNN-short-name`, branched from `dev`, merged back to `dev`
- Commit messages: imperative, sentence case, no AI attribution
- `.gitignore` covers `.env` and `config.py`
- `.env.example` lists every variable with placeholder values
- No license file

## Boundaries

- Never push. Give commands and wait for confirmation.
- Never change app behavior unless a spec says to.
- Never commit `.env`, `config.py`, real IPs, or credentials.
- Never merge a pull request. I review and merge.
- Only write things that are true in the code.

## Workflow

Changes start as specs in `docs/specs/`. Claude Code implements them on a spec branch, and I review and merge every pull request.
