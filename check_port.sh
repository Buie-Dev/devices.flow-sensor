#!/bin/bash

echo "=== USB Serial Port Check ==="
echo ""

# Look for all cu.* ports
PORTS=$(ls /dev/cu.* 2>/dev/null | grep -E "usbserial|usbmodem|SLAB_USBtoUART|wchusbserial|usbjtag")

if [ -z "$PORTS" ]; then
  echo "No ESP32/USB serial port found."
  echo ""
  echo "Things to try:"
  echo "  1. Make sure the USB cable has data lines (try a different cable)"
  echo "  2. Install the CP210x driver: silabs.com → CP210x USB to UART Bridge"
  echo "  3. Unplug and reconnect the ESP32"
  echo "  4. Hold BOOT, tap EN, release BOOT on the ESP32"
  echo ""
  echo "All /dev/cu.* ports currently visible:"
  ls /dev/cu.* 2>/dev/null || echo "  (none)"
  exit 1
fi

echo "Found port(s):"
for PORT in $PORTS; do
  echo "  $PORT"
done

echo ""

# If exactly one port, use it automatically
PORT_COUNT=$(echo "$PORTS" | wc -l | tr -d ' ')

if [ "$PORT_COUNT" -eq 1 ]; then
  SELECTED_PORT=$PORTS
  echo "Using: $SELECTED_PORT"
else
  echo "Multiple ports found. Using the first one: $(echo "$PORTS" | head -1)"
  SELECTED_PORT=$(echo "$PORTS" | head -1)
fi

echo ""
echo "=== USB Device Info ==="
system_profiler SPUSBDataType 2>/dev/null | grep -A 5 -i "esp\|cp210\|ch340\|ft232\|silicon" || echo "(no matching USB device info found)"

echo ""
echo "=== Done ==="
echo "Your port is: $SELECTED_PORT"
echo ""
echo "Use this in your commands, for example:"
echo "  python3 -m esptool -p $SELECTED_PORT erase_flash"
echo "  mpremote connect $SELECTED_PORT ls"
