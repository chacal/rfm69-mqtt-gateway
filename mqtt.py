import paho.mqtt.client as mqtt
import queue

rx_queue_size = 100


class MQTT():
    def __init__(self, mqtt_broker, topic):
        self.rx_queue = queue.Queue(rx_queue_size)
        self.mqtt = mqtt.Client()
        self.__connect_mqtt_client(mqtt_broker, topic)

    def get_message(self):
        try:
            if not self.rx_queue.empty():
                return self.rx_queue.get_nowait()
        except queue.Empty:
            pass
        return None

    def publish_message(self, topic, message):
        self.mqtt.publish(topic, message)

    def __connect_mqtt_client(self, broker, topic):
        self.mqtt.connect(broker)
        self.mqtt.subscribe(topic)
        self.mqtt.message_callback_add(topic, self.__on_message)
        self.mqtt.loop_start()

    def __on_message(self, client, userdata, message):
        try:
            self.rx_queue.put_nowait(message)
        except queue.Full:
            print("MQTT RX queue full! Discarding message.")
