import time
import json
import os
from RFM69 import Radio, FREQ_433MHZ
from mqtt import MQTT
from datetime import datetime
from types import SimpleNamespace
from pprint import pprint

conf = SimpleNamespace(**{
    # MQTT settings
    "mqtt_broker": os.getenv('MQTT_BROKER', "mqtt-home.chacal.fi"),
    "tx_subs_topic": os.getenv('TX_SUBS_TOPIC', "/rfm69gw/tx/+"),
    "rx_topic": os.getenv('RX_TOPIC', "/rfm69gw/rx"),

    # Radio settings
    "node_id": os.getenv('NODE_ID', 1),
    "network_id": os.getenv('NETWORK_ID', 50),
    "radio_power": os.getenv('RADIO_POWER', 80),
    "interrupt_pin": os.getenv('INTERRUPT_PIN', 15),
    "reset_pin": os.getenv('RESET_PIN', 16),
    "spi_bus": os.getenv('SPI_BUS', 0),
    "spi_device": os.getenv('SPI_DEVICE', 1)
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


def forward_from_radio_to_mqtt(radio, mqtt):
    for packet in radio.get_packets():
        radio.send_ack(packet.sender)
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


with Radio(FREQ_433MHZ, conf.node_id, conf.network_id, isHighPower=True, power=conf.radio_power,
           interruptPin=conf.interrupt_pin, resetPin=conf.reset_pin, spiBus=conf.spi_bus, spiDevice=conf.spi_device,
           autoAcknowledge=False) as radio:
    print("rfm69-mqtt-gateway starting..")
    print("Used configuration:")
    pprint(conf.__dict__)

    mqtt = MQTT(conf.mqtt_broker, conf.tx_subs_topic)

    while True:
        forward_from_radio_to_mqtt(radio, mqtt)
        forward_from_mqtt_to_radio(mqtt, radio)
        time.sleep(0.01)
