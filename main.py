import time
import json
import os
import signal
from RFM69 import Radio, FREQ_433MHZ
from mqtt import MQTT
from datetime import datetime
from types import SimpleNamespace
from pprint import pprint
from collections import deque

conf = SimpleNamespace(**{
    # MQTT settings
    "mqtt_broker": os.getenv('MQTT_BROKER', "mqtt-home.chacal.fi"),
    "tx_subs_topic": os.getenv('TX_SUBS_TOPIC', "/rfm69gw/tx/+"),
    "rx_topic": os.getenv('RX_TOPIC', "/rfm69gw/rx"),

    # Radio settings
    "node_id": int(os.getenv('NODE_ID', 1)),
    "network_id": int(os.getenv('NETWORK_ID', 50)),
    "radio_power": int(os.getenv('RADIO_POWER', 80)),
    "interrupt_pin": int(os.getenv('INTERRUPT_PIN', 15)),
    "reset_pin": int(os.getenv('RESET_PIN', 16)),
    "spi_bus": int(os.getenv('SPI_BUS', 0)),
    "spi_device": int(os.getenv('SPI_DEVICE', 1)),
    "rx_buffer_len_ms": int(os.getenv('RX_BUFFER_LEN_MS', 200))
})


def to_json(radio_packet):
    ret = {
        "rssi": radio_packet.RSSI,
        "sender": radio_packet.sender,
        "receiver": radio_packet.receiver,
        "data": "".join(["%02X" % n for n in radio_packet.data]),
        "ts": datetime.utcnow().isoformat() + 'Z'
    }
    return json.dumps(ret)


def already_received(radio_packet):
    global rx_buffer
    now = datetime.utcnow().timestamp()
    previously_received = next((p for p in rx_buffer if now - p.received.timestamp() < conf.rx_buffer_len_ms / 1000 and radio_packet.data == p.data), False)
    rx_buffer.append(radio_packet)
    return True if previously_received else False


def forward_from_radio_to_mqtt(radio, mqtt):
    for packet in radio.get_packets():
        if not already_received(packet):
            mqtt.publish_message(conf.rx_topic, to_json(packet))


def forward_from_mqtt_to_radio(mqtt, radio):
    msg_to_transmit = mqtt.get_message()
    if msg_to_transmit:
        receiver_str = msg_to_transmit.topic.split("/")[-1]
        try:
            receiver = int(receiver_str)
            ret = radio.send(receiver, list(msg_to_transmit.payload))
            print("Sent packet to %s. Acked: %s" % (receiver, ret))
        except ValueError:
            print("Invalid RFM69 receiver: %s" % receiver_str)


def handle_stop_signals(signum, frame):
    global running
    print("Received signal %d." % signum)
    running = False


running = True
rx_buffer = deque(maxlen = 10)

with Radio(FREQ_433MHZ, conf.node_id, conf.network_id, isHighPower=True, power=conf.radio_power,
           interruptPin=conf.interrupt_pin, resetPin=conf.reset_pin, spiBus=conf.spi_bus, spiDevice=conf.spi_device,
           autoAcknowledge=False) as radio:
    signal.signal(signal.SIGINT, handle_stop_signals)
    signal.signal(signal.SIGTERM, handle_stop_signals)

    print("rfm69-mqtt-gateway starting..")
    print("Used configuration:")
    pprint(conf.__dict__)

    mqtt = MQTT(conf.mqtt_broker, conf.tx_subs_topic)

    while running:
        forward_from_radio_to_mqtt(radio, mqtt)
        forward_from_mqtt_to_radio(mqtt, radio)
        time.sleep(0.005)

    print("Disconnecting MQTT.")
    mqtt.disconnect()

print("Exiting.")