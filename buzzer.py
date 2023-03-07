from actuator import Actuator
import time, json, queue, signal
from rpi_hardware_pwm import HardwarePWM

class Buzzer(Actuator):
    _queue = queue.Queue()
    _signal_map = {"SIGFIN": [(400,0.5)],
                   "SIGERR": [(200,0.5)],
                   "SIGRCV": [(860,0.25),(0,0.25),(860,0.25)]}
    def __init__(self):
        super().__init__()
        with open("buzz_cfg.json") as file:
            self._channel = json.load(file)["channel"]
        self._pwm = HardwarePWM(pwm_channel=self._channel, hz=500)
        self._pwm.change_duty_cycle(50)
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
        combo = self._signal_map.get(signal,[(0,0)])
        for note in combo:
            if note[0]:
                self._pwm.change_frequency(note[0])
                self._pwm.start(50)
            else:
                self._pwm.stop()
            time.sleep(note[1])
        self._pwm.stop()
        return

    def end(self):
        self._queue.put("SIGTERM")
        self._client.disconnect()
        self._client.loop_stop()
        self.running = False
        return

    def main(self):
        self.start_loop()
        while self.running:
            try:
                sig = self._queue.get(timeout=5)
            except queue.Empty as e:
                continue
            print("playing",sig)
            self.actuate(sig)
        return

    def sigterm(self,sig,frame):
        self.end()
        return

if __name__ == "__main__":
    display = Buzzer()
    display.start_loop()
    display.main()