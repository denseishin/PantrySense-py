from actuator import Actuator
import time, json, queue, signal
import RPi.GPIO as GPIO

class LEDs(Actuator):
    _queue = queue.Queue()
    _signal_map = {"SIGRDY": (True,False,False),
                   "SIGERR": (False,False,True),
                   "SIGPRC": (False,True,False), #processing
                   "SIGCLS": (False,False,False), #?clear screen?
                   "SIGTERM": (False,False,False)}
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        super().__init__()
        with open("led_cfg.json") as file:
            self._led_map = json.load(file)
        for color in self._led_map.keys():
            pin = self._led_map[color]
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin,True)
        self._s_topic = "regal/ctrlsig"
        self._client.on_connect = self._sub_on_connect
        self._client.on_message = self.onSignal
        self._client.connect(self._host,self._port,60)
        self.running = True

    def start_loop(self):
        self._client.loop_start()
        signal.signal(signal.SIGTERM, self.sigterm)
        return

    def onSignal(self,client,userdata,message):
        msg = message.payload.decode("utf-8")
        if msg in self._signal_map.keys():
            self._queue.put(msg)
        return

    def actuate(self,signal):
        combo = self._signal_map[signal]
        GPIO.output(self._led_map["green"],combo[0])
        GPIO.output(self._led_map["yellow"],combo[1])
        GPIO.output(self._led_map["red"],combo[2])
        return

    def reset_leds(self):
        GPIO.output(self._led_map["green"],False)
        GPIO.output(self._led_map["yellow"],False)
        GPIO.output(self._led_map["red"],False)
        return

    def end(self):
        self._queue.put("SIGTERM")
        self._client.disconnect()
        self._client.loop_stop()
        self.running = False
        GPIO.cleanup()
        return

    def main(self):
        self.start_loop()
        while self.running:
            #self.reset_leds()
            try:
                sig = self._queue.get(timeout=5)
            except queue.Empty as e:
                continue
            print(sig)
            self.actuate(sig)
        return

    def sigterm(self,sig,frame):
        self.end()
        return

if __name__ == "__main__":
    display = LEDs()
    display.start_loop()
    display.main()