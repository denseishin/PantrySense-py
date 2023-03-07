from baseclient import BaseClient
import time, json

class Actuator(BaseClient):
    _s_topic = ""
    def __init__(self, mqttconf = "default_mqtt.json"):
        super().__init__(mqttconf)
        print("init actuator")

    def init_actuator(self):
        raise NotImplementedError("Please implement this method")

    def start_loop(self):
        raise NotImplementedError("Please implement this method")

    def onSignal(self,client,userdata,message):
        raise NotImplementedError("Please implement this method")

    def actuate(self,signal):
        raise NotImplementedError("Please implement this method")

    def end(self):
        raise NotImplementedError("Please implement this method")

    def _sub_on_connect(self, client, userdata, flags, rc, prop):
        self._client.subscribe(self._s_topic)
        return
