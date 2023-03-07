from actuator import Actuator
import time, json, queue, signal
import playsound

class Buzzer(Actuator):
    _queue = queue.Queue()
    _signal_map = {"SIGFIN": 'audio/finish.wav',
                   "SIGERR": 'audio/error.wav',
                   "SIGRCV": 'audio/received.wav'}
    def __init__(self):
        super().__init__()
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
        audiofile = self._signal_map.get(signal,False)
        if audiofile:
            print("playing",audiofile)
            playsound.playsound(audiofile)
        else:
            print('file not specified')
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