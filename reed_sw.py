from sensor import Sensor
import json, signal, time
import RPi.GPIO as GPIO

class Reedswitch(Sensor):
    _gpio_in = 99
    def __init__(self):
        super().__init__()
        with open("reed_cfg.json") as file:
            self._gpio_in = json.load(file)["pin"]

    def init_sensor(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._gpio_in, GPIO.IN)
        self._p_topics = ["regal/reed/1"]
        return

    def start_loop(self):
        signal.signal(signal.SIGTERM, self.sigterm)
        GPIO.add_event_detect(self._gpio_in, edge=GPIO.BOTH, callback=self.sensor_callback, bouncetime=200)
        self._client.connect(self._host,self._port,60)
        self._client.loop_forever()
        return

    def sensor_callback(self,data=0):
        state = GPIO.input(self._gpio_in)
        self.send(self._p_topics[0],state)
        return

    def send(self, topic, data):
        self._client.publish(topic,int(data),retain=True)
        return

    def end(self):
        self._client.disconnect()
        GPIO.cleanup()
        return

    def sigterm(self,sig,frame):
        self.end()
        return


if __name__ == '__main__':
    rsw = Reedswitch()
    rsw.init_sensor()
    rsw.start_loop()
