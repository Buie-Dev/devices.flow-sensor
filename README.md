# DIGITEN FL-608 Flow Sensor + ESP32 — MicroPython MQTT Setup Guide

## Overview

This guide covers everything needed to wire a DIGITEN FL-608 hall effect flow sensor to an
ESP32 NodeMCU and run a MicroPython script that publishes flow data over MQTT. The script
publishes pulse counts and calculated flow rate to `irrigation/flow` every 5 seconds, and
responds to health check pings on `healthcheck/request`.

---

## Hardware Required

- DIGITEN FL-608 G3/4" water flow sensor
- ESP32 NodeMCU development board
- USB cable (Micro-USB or USB-C depending on your board)
- 10kΩ resistor (optional — for external pull-up on signal wire)
- Jumper wires

---

## Wiring

The sensor has three wires. Connect them to the ESP32 as follows:

| Wire colour | Wire label | ESP32 pin             | Notes                      | Pull-up               |
|-------------|------------|-----------------------|----------------------------|-----------------------|
| Red         | VCC        | 3.3V or VIN           | 5V preferred (VIN = USB 5V)| —                     |
| Black       | GND        | GND                   | Common ground              | —                     |
| Yellow      | Signal     | GPIO 14               | Hall effect pulse output   | 10kΩ to 3.3V optional |

> **Pull-up note:** The pull-up resistor is optional. The code enables the ESP32 internal
> pull-up automatically. Only add a physical 10kΩ resistor if you get erratic pulse counts.

---

## MQTT Topics

| Action    | Topic                  | Description                                      |
|-----------|------------------------|--------------------------------------------------|
| Publish   | `irrigation/flow`      | Pulse count, flow rate, volume — every 5 seconds |
| Subscribe | `healthcheck/request`  | Listens for any health check ping                |
| Publish   | `healthcheck/response` | Responds with sensor name and status OK          |

Example payload published to `irrigation/flow`:

```json
{
  "sensor": "irrigation/flowSensor",
  "pulse_count": 45,
  "flow_rate_lpm": 0.818,
  "volume_L": 0.00136,
  "elapsed_s": 5.0
}
```

---

## Computer Setup

### Step 1 — Check your Python version

```bash
python3 --version
```

You need Python 3.10 or higher for the latest esptool. If you are on 3.9 (common with
Anaconda), use `python3 -m esptool` throughout this guide instead of the `esptool` command
directly — it works regardless of version.

### Step 2 — Install esptool and mpremote

```bash
pip3 install esptool mpremote
```

If you get an "externally managed environment" error:

```bash
pip3 install esptool mpremote --break-system-packages
```

> **Note:** If the `esptool` command is not found after installing, use `python3 -m esptool`
> instead. This bypasses PATH issues common with Anaconda.

### Step 3 — Install the CP210x USB driver (Mac only)

Most ESP32 NodeMCU boards use a CP2102 USB chip. If your board does not appear as a serial
port after plugging in, download and install the CP210x driver from Silicon Labs:

**silabs.com → Products → Interface → USB Bridges → CP210x USB to UART Bridge**

Unplug and reconnect the ESP32 after installing.

---

## Finding Your Serial Port

Run this without the ESP32 plugged in, then plug it in and run it again:

```bash
ls /dev/cu.*
```

The new entry that appears is your port. Common names:

- `/dev/cu.SLAB_USBtoUART` — most common with NodeMCU + CP2102 chip
- `/dev/cu.usbserial-0001`
- `/dev/cu.usbmodem*`

On **Windows**, open Device Manager → Ports (COM & LPT).  
On **Linux**, run `ls /dev/ttyUSB*`.

---

## Flashing MicroPython Firmware

### Step 1 — Download the firmware

Go to [micropython.org/download/ESP32_GENERIC](https://micropython.org/download/ESP32_GENERIC)
and download the latest stable `.bin` file from the **Firmware** section at the top. Do not
use the SPIRAM, Unicore, or OTA variants — the standard build is correct for the ESP32-D0WD.

### Step 2 — Erase existing flash

Replace `/dev/cu.SLAB_USBtoUART` with your actual port:

```bash
python3 -m esptool -p /dev/cu.SLAB_USBtoUART erase_flash
```

> **If it hangs at `Connecting......`:** Hold the **BOOT** button on the ESP32, tap **EN**
> (reset) once, release BOOT, then run the command again immediately.

### Step 3 — Flash MicroPython

Replace the filename with the exact `.bin` you downloaded:

```bash
python3 -m esptool --chip esp32 -p /dev/cu.SLAB_USBtoUART --baud 460800 \
  write_flash -z 0x1000 ~/Downloads/ESP32_GENERIC-20260406-v1.28.0.bin
```

A progress bar will appear. The process takes about 30 seconds.

---

## Configuring the Script

Before uploading, open `flow_sensor_mqtt.py` in a text editor and set these values at the
top of the file:

```python
WIFI_SSID         = "your_wifi_ssid"
WIFI_PASSWORD     = "your_wifi_password"
MQTT_BROKER       = "192.168.1.100"   # your broker IP
MQTT_PORT         = 1883
MQTT_USER         = ""                 # leave blank if no auth
MQTT_PASSWORD     = ""
FLOW_PIN          = 14                 # GPIO pin for signal wire
PUBLISH_INTERVAL_MS = 5000            # publish every 5 seconds
```

---

## Uploading the Script

MicroPython runs `main.py` automatically on boot. Upload your configured script as `main.py`:

```bash
mpremote connect /dev/cu.SLAB_USBtoUART cp flow_sensor_mqtt.py :main.py
```

If the file is in your Downloads folder:

```bash
mpremote connect /dev/cu.SLAB_USBtoUART cp ~/Downloads/flow_sensor_mqtt.py :main.py
```

Verify the upload:

```bash
mpremote connect /dev/cu.SLAB_USBtoUART ls
```

---

## Testing

Open the serial monitor to watch boot output in real time:

```bash
mpremote connect /dev/cu.SLAB_USBtoUART repl
```

Press `Ctrl+]` (right square bracket) to exit.

### Expected output
Flow sensor interrupt configured on GPIO 14
Connecting to WiFi: YourNetworkName
WiFi connected: 192.168.1.55
MQTT connected to 192.168.1.100, subscribed to healthcheck/request
Running — publishing every 5 seconds
Published: {"sensor": "irrigation/flowSensor", "pulse_count": 0, "flow_rate_lpm": 0.0 ...}

### Testing the health check

Publish any message to `healthcheck/request` from your MQTT client. The ESP32 will
immediately respond on `healthcheck/response`:

```json
{"sensor": "irrigation/flowSensor", "status": "ok"}
```

---

## Flow Rate Calibration

The default calibration is `330` pulses per litre, derived from the FL-608 spec formula
`F = 5.5 × Q` (Q in L/min). To verify this against your actual sensor, flow exactly 1 litre
through the sensor into a measuring jug and check the reported pulse count. Update
`PULSES_PER_LITRE` in the script to match.

---

## Troubleshooting

### Board not detected / Connecting hangs

- Hold BOOT, tap EN, release BOOT, then run the esptool command immediately
- Add `--baud 115200` to slow the connection speed
- Try a different USB cable — many are charge-only with no data lines
- Install the CP210x driver if the port never appears after plugging in

### WiFi not connecting

- SSID and password are case sensitive
- ESP32 only supports 2.4GHz — it will not connect to 5GHz networks
- Move closer to the router if signal is weak

### MQTT not connecting

- Confirm the broker IP is correct and the broker is running
- Check port 1883 is not blocked by a firewall
- Set `MQTT_USER` and `MQTT_PASSWORD` if your broker requires authentication

### Zero pulse count when water is flowing

- Confirm the yellow wire is on GPIO 14
- Check VCC is connected — the sensor makes a faint click when water flows if powered
- Add a physical 10kΩ pull-up resistor between signal and 3.3V
- Confirm GPIO 14 is not in use by another peripheral

### Ctrl+] not exiting the REPL

Press `Ctrl+C` first to stop the running script, then `Ctrl+]` to exit. Make sure you are
pressing the right square bracket `]` and not the letter J.