from baseclient import BaseClient
import time, json

class Sensor(BaseClient):
    _p_topics = []
    def __init__(self, mqttconf = "default_mqtt.json"):
        super().__init__(mqttconf)
        print("init sensor")

    def init_sensor(self):
        raise NotImplementedError("Please implement this method")

    def start_loop(self):
        raise NotImplementedError("Please implement this method")

    def sensor_poll(self):
        raise NotImplementedError("Please implement this method")

    def sensor_callback(self,data):
        raise NotImplementedError("Please implement this method")

    def send(self, topic, data):
        raise NotImplementedError("Please implement this method")

    def end(self):
        raise NotImplementedError("Please implement this method")