from sensor import Sensor
import json, signal, time
import RPi.GPIO as GPIO

class Buttons(Sensor):
    _gpio_in = 99
    def __init__(self):
        super().__init__()
        with open("btn_cfg.json") as file:
            self._btn_gpio = json.load(file)["pins"]
        self._btn_map = dict()
        for n in range(0,len(self._btn_gpio)):
            self._btn_map[str(self._btn_gpio[n])] = n
        self._client.connect(self._host,self._port,60)

    def init_sensor(self):
        GPIO.setmode(GPIO.BCM)
        for pin in self._btn_gpio:
            GPIO.setup(pin, GPIO.IN)
        self._p_topics = ["regal/btn/"]
        return 

    def start_loop(self):
        signal.signal(signal.SIGTERM, self.sigterm)
        for pin in self._btn_gpio:
            GPIO.add_event_detect(pin, edge=GPIO.BOTH, callback=self.sensor_callback, bouncetime=200)
        self._client.loop_forever()
        return

    def sensor_callback(self,data):
        state = GPIO.input(data)
        topic = self._p_topics[0] + str(self._btn_map[str(data)])
        #print(data,state)
        self.send(topic,state)
        return

    def send(self, topic, data):
        self._client.publish(topic,int(data),retain=False)
        return

    def end(self):
        self._client.disconnect()
        GPIO.cleanup()
        return

    def sigterm(self,sig,frame):
        self.end()
        return


if __name__ == '__main__':
    btn = Buttons()
    btn.init_sensor()
    btn.start_loop()
