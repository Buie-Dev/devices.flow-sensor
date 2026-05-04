#!/bin/bash

# Erases the ESP32 flash and writes a MicroPython firmware image.
# Run this once before the first upload.sh, or to recover a device.
#
# The .bin firmware file can be in this directory OR ~/Downloads/.
# Download from: https://micropython.org/download/ESP32_GENERIC/

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="/dev/cu.SLAB_USBtoUART"

echo "=== ESP32 Flow Sensor Flash ==="
echo ""

# ─── Check port ───────────────────────────────────────────────
if [ ! -e "$PORT" ]; then
  echo "ERROR: Port $PORT not found."
  echo ""
  echo "  - Try a different USB cable (many are charge-only)"
  echo "  - Install the CP210x driver from Silicon Labs"
  echo "  - Hold BOOT, tap EN, release BOOT on the ESP32"
  echo "  - Run ./check_port.sh to find your port"
  exit 1
fi

echo "Port: $PORT"
echo ""

# ─── Find firmware .bin (this dir first, then ~/Downloads) ────
BIN_FILE=$(ls "$SCRIPT_DIR"/*.bin 2>/dev/null | head -1)
if [ -z "$BIN_FILE" ]; then
  BIN_FILE=$(ls ~/Downloads/ESP32_GENERIC*.bin 2>/dev/null | sort | tail -1)
fi

if [ -z "$BIN_FILE" ]; then
  echo "ERROR: No MicroPython .bin found."
  echo ""
  echo "  Download from: https://micropython.org/download/ESP32_GENERIC/"
  echo "  Place it in this directory or ~/Downloads/ and re-run."
  exit 1
fi

echo "Firmware: $BIN_FILE"
echo ""

# ─── Step 1: Erase flash ──────────────────────────────────────
echo "Step 1/2 — Erasing flash..."
echo "  (If it hangs at 'Connecting......': hold BOOT, tap EN, release BOOT)"
echo ""
python3 -m esptool -p "$PORT" erase_flash
if [ $? -ne 0 ]; then
  echo "ERROR: Erase failed."
  exit 1
fi

echo ""

# ─── Step 2: Flash MicroPython ────────────────────────────────
echo "Step 2/2 — Flashing MicroPython..."
python3 -m esptool --chip esp32 -p "$PORT" --baud 460800 \
  write_flash -z 0x1000 "$BIN_FILE"

if [ $? -ne 0 ]; then
  echo "ERROR: Flash failed."
  exit 1
fi

echo ""
echo "=== Flash complete ==="
echo "Run ./upload.sh to deploy the sensor code."
