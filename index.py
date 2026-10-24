"""
DIGITEN FL-608 Flow Sensor — MicroPython for ESP32
MQTT Topics:
  Publish:   irrigation/flow       (pulse count + pulse rate every interval)
  Subscribe: healthcheck/request   (any message triggers health response)
  Publish:   healthcheck/response  (sensor name confirmation)

Litre conversion is handled by irrigation-controller.
"""

import network
import time
import json
from machine import Pin
from umqtt.simple import MQTTClient
from config import (
    WIFI_SSID,
    WIFI_PASSWORD,
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USER,
    MQTT_PASSWORD,
    SENSOR_NAME,
)

MQTT_CLIENT = SENSOR_NAME
FLOW_PIN = 14  # GPIO pin connected to sensor signal wire
PUBLISH_INTERVAL_MS = 1000  # publish every 1 second

# MQTT topics
TOPIC_FLOW_PUBLISH = b"irrigation/flow"
TOPIC_HEALTH_SUBSCRIBE = b"healthcheck/request"
TOPIC_HEALTH_PUBLISH = b"healthcheck/response"

# ─────────────────────────────────────────
# GLOBALS
# ─────────────────────────────────────────
pulse_count = 0
last_pub_time = 0
last_ping_time = 0
client = None

PING_INTERVAL_MS = 30000  # ping broker every 30s to maintain keepalive


# ─────────────────────────────────────────
# INTERRUPT HANDLER
# ─────────────────────────────────────────
def pulse_isr(pin):
    global pulse_count
    pulse_count += 1


# ─────────────────────────────────────────
# WIFI
# ─────────────────────────────────────────
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    while not wlan.isconnected():
        print(f"Connecting to WiFi: {WIFI_SSID}")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 15
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print(".", end="")
        print()
        if not wlan.isconnected():
            print("WiFi failed, retrying in 10s...")
            time.sleep(10)
    print(f"WiFi connected: {wlan.ifconfig()[0]}")


# ─────────────────────────────────────────
# MQTT CALLBACK (incoming messages)
# ─────────────────────────────────────────
def mqtt_callback(topic, msg):
    print(f"MQTT rx [{topic}]: {msg}")
    if topic == TOPIC_HEALTH_SUBSCRIBE:
        # Respond with sensor name on healthcheck/response
        payload = json.dumps({"device": SENSOR_NAME})
        client.publish(TOPIC_HEALTH_PUBLISH, payload)
        print(f"Health check responded: {payload}")


# ─────────────────────────────────────────
# MQTT CONNECT
# ─────────────────────────────────────────
def connect_mqtt():
    global client
    c = MQTTClient(
        client_id=MQTT_CLIENT,
        server=MQTT_BROKER,
        port=MQTT_PORT,
        user=MQTT_USER or None,
        password=MQTT_PASSWORD or None,
        keepalive=60,
    )
    c.set_callback(mqtt_callback)
    c.connect()
    c.subscribe(TOPIC_HEALTH_SUBSCRIBE)
    print(f"MQTT connected to {MQTT_BROKER}, subscribed to {TOPIC_HEALTH_SUBSCRIBE}")
    client = c


# ─────────────────────────────────────────
# PUBLISH FLOW DATA
# ─────────────────────────────────────────
def publish_flow():
    global pulse_count, last_pub_time

    now = time.ticks_ms()
    elapsed_s = time.ticks_diff(now, last_pub_time) / 1000.0

    # Snapshot and reset pulse count atomically-ish
    # (MicroPython ISRs are cooperative on ESP32, this is safe)
    count = pulse_count
    pulse_count = 0
    last_pub_time = now

    payload = json.dumps(
        {
            "sensor": SENSOR_NAME,
            "pulse_count": count,
            "elapsed_s": round(elapsed_s, 2),
        }
    )

    client.publish(TOPIC_FLOW_PUBLISH, payload)
    print(f"Published: {payload}")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    global last_pub_time
    time.sleep_ms(10000)
    print("Waiting for 10 seconds...")
    # Setup flow sensor pin with internal pull-up, interrupt on falling edge
    flow_pin = Pin(FLOW_PIN, Pin.IN, Pin.PULL_UP)
    flow_pin.irq(trigger=Pin.IRQ_FALLING, handler=pulse_isr)
    print(f"Flow sensor interrupt configured on GPIO {FLOW_PIN}")

    connect_wifi()

    while True:
        try:
            connect_mqtt()
            break
        except Exception as e:
            print(f"MQTT connection failed: {e} — retrying in 10s...")
            time.sleep(10)

    last_pub_time = time.ticks_ms()
    last_ping_time = time.ticks_ms()

    print("Running — publishing every", PUBLISH_INTERVAL_MS // 1000, "seconds")

    while True:
        try:
            # Check for incoming MQTT messages (non-blocking)
            client.check_msg()

            now = time.ticks_ms()

            # Publish on interval
            if time.ticks_diff(now, last_pub_time) >= PUBLISH_INTERVAL_MS:
                publish_flow()

            # Keepalive ping so the broker doesn't drop the connection
            if time.ticks_diff(now, last_ping_time) >= PING_INTERVAL_MS:
                client.ping()
                last_ping_time = now
                print("MQTT ping sent")

            time.sleep_ms(100)

        except OSError as e:
            print(f"MQTT error: {e} — reconnecting in 5s")
            time.sleep(5)
            connect_wifi()  # Re-establish WiFi first if it dropped
            try:
                connect_mqtt()
                last_ping_time = time.ticks_ms()
            except Exception as e2:
                print(f"Reconnect failed: {e2}")


if __name__ == "__main__":
    main()
