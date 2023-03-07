import paho.mqtt.client as mqttc
import json, time

class BaseClient(object):
    _client = mqttc.Client(protocol=5,transport="tcp")
    _host = "127.0.0.1"
    _port = 1883
    _username = "default"
    _pw = "default"

    def __init__(self, mqttconf = "default_mqtt.json"):
        self._load_mqtt_cfg(mqttconf)
        self._client.username_pw_set(self._username,self._pw)

    def _load_mqtt_cfg(self, file = "default_mqtt.json"):
        with open(file) as file:
            conf = json.load(file)
            self._host = conf["host"]
            self._port = conf["port"]
            self._username = conf["username"]
            self._pw = conf["pw"]
        return

    def _test_on_connect(self, client, userdata, flags, rc, prop):
        #print("connected")
        self._client.subscribe("test")
        return

    def _test_on_signal(self, client, userdata, message):
        print(message.topic,str(message.payload))
        return

    def test_connect(self):
        self._load_mqtt_cfg()
        #self._client.enable_logger()
        #self._client.on_log = self._log
        self._client.on_connect = self._test_on_connect
        self._client.on_message = self._test_on_signal
        #self._client.on_disconnect = self.on_disconnect
        self._client.username_pw_set(self._username,self._pw)
        self._client.connect(self._host,self._port,60)
        return

    def on_disconnect(self,client,userdata,rc, what):
        #print('disconnect')
        print(client,userdata,rc,what)

    def _log(self, client, userdata, level, buf):
        print("log:",buf)
        return

    def test_loop(self):
        self._client.loop_forever()
        return

if __name__ == "__main__":
    mqtt_bc = BaseClient()
    mqtt_bc.test_connect()
    mqtt_bc.test_loop()