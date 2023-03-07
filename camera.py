from sensor import Sensor
from actuator import Actuator
import json, signal, time, datetime, multiprocessing, cv2, threading, queue, base64
#import RPi.GPIO as GPIO

class MqttCam (Sensor, Actuator):
    _process_count = 3
    _photoqueue = multiprocessing.Queue(_process_count)
    _camsignalqueue = queue.Queue()
    _ctrlsignalqueue = queue.Queue()
    _resultqueue = multiprocessing.Queue()
    _cam_status = False #threading.Semaphore(0)
    _running = True
    _last_ldr = 0.0
    _last_door = False
    _door_state = False
    _last_barcode = None
    _last_barcode_ts = 0

    def __init__(self):
        Sensor.__init__(self)
        self._s_topics = ["regal/reed/1","regal/btn/#","regal/ldr/1"]
        with open("cam_cfg.json") as file:
            cfg = json.load(file)
            self._cam_addr = cfg["cam_addr"]
            self._gpio_out = cfg["cam_gpio"]
            self._cam_height = cfg["height"]
            self._cam_width = cfg["width"]

    def init_sensor(self):
        self._cam_stream = cv2.VideoCapture(self._cam_addr)
        self._cam_stream.set(3,self._cam_width) #640#1280)
        self._cam_stream.set(4,self._cam_height) #480#720)
        self._send_thread = threading.Thread(target=self.send_loop)
        self._poll_thread = threading.Thread(target=self.sensor_poll)
        return

    def init_actuator(self):
        #GPIO.setmode(GPIO.BCM)
        #GPIO.setup(self._gpio_out,GPIO.OUT)
        self._gpio_state = False
        #GPIO.output(self._gpio_out,self._gpio_state)
        self._act_thread = threading.Thread(target=self.actuate_loop)
        return

    def onSignal(self,client,userdata,message):
        signal = ""
        #print(message.topic,message.payload)
        src_topics = message.topic.split("/")
        device = src_topics[-2]
        dev_nr = int(src_topics[-1])
        #print(device,dev_nr)
        if device == "btn":
            btnsig = not bool(int(message.payload))
            if btnsig:
                if dev_nr == 1:
                    signal = "photo"
                elif dev_nr == 2:
                    signal = "reserved"
                elif dev_nr == 3:
                    signal = "reserved"
        elif device == "reed":
            if dev_nr == 1:
                roff = bool(int(message.payload))
                #print(roff)
                self._last_door = not roff
                signal = "chkdoor"
        elif device == "ldr":
            if dev_nr == 1:
                ldrval = float(int(message.payload))
                self._last_ldr = ldrval
                signal = "chkdoor"
        self._ctrlsignalqueue.put(signal)
        return

    def actuate(self,signal):
        if signal == "photo":
            self._camsignalqueue.put("photo")
        elif signal == "night_on":
            self.set_nightmode(True)
        elif signal == "night_off":
            self.set_nightmode(False)
        elif signal == "chkdoor":
            self._door_state = self.refresh_cam_status()
        return

    def set_nightmode(self,mode):
        self._gpio_state = True
        #GPIO.output(self._gpio_out,self._gpio_state)

    def refresh_cam_status(self):
        curr_state = self._last_door and self._last_ldr < 10.0
        #print("door state:",curr_state,self._door_state,self._last_door,self._last_ldr)
        if curr_state is not self._door_state:
            if curr_state: #door open
                print("starting camera")
                self._cam_status = True #.release()
            else:
                print("stopping camera")
                self._cam_status = False #.acquire()
        return curr_state

    def end(self):
        print("loop running bool")
        self._running = False
        self._cam_status = False
        print("sending queue end msgs")
        self._ctrlsignalqueue.put(None)
        for _ in range(0,self._process_count+1):
            self._photoqueue.put(((None,None,None),None))
        self._resultqueue.put("RIP")
        print("DC")
        self._client.disconnect()
        print("thread join")
        self._send_thread.join()
        self._act_thread.join()
        self._poll_thread.join()
        print("process kill & join")
        for p in self._frame_procs:
            p.terminate()
            p.join()
        print("threads & processes ended")
        q_empty = False
        #Empty queues!
        while not q_empty:
            try:
                self._ctrlsignalqueue.get(False)
            except queue.Empty as em:
                q_empty = True
        q_empty = False
        while not q_empty:
            try:
                self._photoqueue.get(False)
            except queue.Empty as em:
                q_empty = True
                #self._photoqueue.close()
        q_empty = False
        while not q_empty:
            try:
                self._resultqueue.get(False)
            except queue.Empty as em:
                q_empty = True
                self._resultqueue.close()
        print("queues emptied!")
        #GPIO.cleanup()
        return

    def start_loop(self):
        self._act_thread.start()
        self._client.on_connect = self._sub_on_connect
        self._client.on_message = self.onSignal
        con = self._client.connect(self._host,self._port,60)
        self._client.loop_start()
        self._send_thread.start()
        self._frame_procs = list()
        for n in range(0,self._process_count):
            frameproc = multiprocessing.Process(target=self.sensor_process,args=(self._photoqueue,self._resultqueue))
            frameproc.daemon = True
            frameproc.start()
            self._frame_procs.append(frameproc)
        self._poll_thread.start()
        print("threads & processes started")
        signal.signal(signal.SIGTERM, self.sigterm)
        return

    def sensor_poll(self):
        start = datetime.datetime.now(datetime.timezone.utc)
        framecount = 0
        command = 0
        while self._running:
            #ac = self._cam_status #.acquire(timeout=1)
            #print("ac lock")
            while self._cam_status:
                #print("lock successful, cam read attempt")
                try:
                    command = self._camsignalqueue.get(block=False)
                except queue.Empty as em:
                    command = False
                ret, frame = self._cam_stream.read()
                pictime = datetime.datetime.now(datetime.timezone.utc).timestamp()
                #self._cam_status.release()
                if ret:
                    framecount += 1
                    frame = cv2.rotate(frame,cv2.ROTATE_90_COUNTERCLOCKWISE)
                    self._photoqueue.put(((1,command,pictime),frame))
                    #print("photo cap")
                else:
                    continue
                    #print("no frame")
            time.sleep(1.0/25.0)
        time.sleep(1)
        end = datetime.datetime.now(datetime.timezone.utc)
        self._cam_stream.release()
        #self._photoqueue.close()
        fps = framecount / (end - start).total_seconds()
        print(fps,"fps")
        return

    def actuate_loop(self):
        while True:
            sig = self._ctrlsignalqueue.get()
            if sig:
                print("signal received",sig)
                self.actuate(sig)
            elif sig is None:
                break

    def sensor_callback(self,data):
        return

    def sigterm(self,sig,frame):
        self.end()
        return

    def _sub_on_connect(self, client, userdata, flags, rc, prop):
        for topics in self._s_topics:
            self._client.subscribe(topics)
        return

    def sensor_process(self,imgqueue,resqueue):
        barcget = cv2.barcode_BarcodeDetector()
        result = dict()
        while True:
            modeinfo, frame = imgqueue.get()
            sig = modeinfo[1]
            mode = modeinfo[0]
            ts = modeinfo[2]
            result.clear()
            if frame is None:
                #print("terminating!")
                break
            #print("consoom")
            if mode == 1:
                ok, info, type, corners = barcget.detectAndDecode(frame)
                if ok and (type[0] >= 1 and type[0] <= 3):
                    result["code"] = info[0]
                    result["type"] = type[0]
            if sig == "photo":
                result["photo"] = cv2.imencode('.png',frame)[1].tobytes()
            if result:
                result["timestamp"] = ts
                resqueue.put(result)
        #print("process terminated")
        return

    def send_loop(self):
        while True:
            msg = self._resultqueue.get()
            if msg == "RIP":
                break
            else:
                #print(msg)
                if "photo" in msg.keys():
                    msg["code"] = self._last_barcode
                    msg["photo"] = base64.b64encode(msg["photo"]).decode('ascii')
                    self.send("regal/camera/1/photo",json.dumps(msg))
                if "code" in msg.keys():
                    print(msg["code"], msg["type"])
                    if self._last_barcode == msg["code"]:
                        if (msg["timestamp"] - self._last_barcode_ts) > 3.0:
                            self.send("regal/camera/1/barcode",json.dumps(msg))
                            print("sent")
                            self._last_barcode_ts = msg["timestamp"]
                    else:
                        self.send("regal/camera/1/barcode",json.dumps(msg))
                        print("sent")
                        self._last_barcode = msg["code"]
                        self._last_barcode_ts = msg["timestamp"]

    def send(self, topic, data):
        self._client.publish(topic,data,retain=False)
        return

if __name__ == '__main__':
    cam = MqttCam()
    cam.init_sensor()
    cam.init_actuator()
    cam.start_loop()
    running = True
    while running:
        com = input("command\n")
        if com == "end":
            running = False
            cam.end()
    #cam.sensor_poll()
