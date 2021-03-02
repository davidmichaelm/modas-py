from gpiozero import MotionSensor, LED, Button
from picamera import PiCamera
from time import sleep
import datetime as dt
import random
import requests
import json

class Modas:
    def __init__(self):
        # init PiCamera
        self.camera = PiCamera()
        # set camera resolution
        #self.camera.rotation = 180
        self.camera.resolution = (800,600)
        # init green, red LEDs
        self.green = LED(25)
        self.red = LED(24)
        # init button
        self.button = Button(8)
        # init PIR
        self.pir = MotionSensor(12)
        
        # when button  is released, toggle system arm / disarm
        self.button.when_released = self.toggle
        
        # system is disarmed by default
        self.armed = False
        self.disarm_system()
        
    def init_alert(self):
        self.green.off()
        self.red.blink(on_time=.25, off_time=.25, n=None, background=True)
        print("motion detected")
        
        timestamp = dt.datetime.now()
        
        # Take photo
        self.snap_photo(timestamp)
        
        flagged = False
        location = self.get_random_location()
        
        response = self.post_event(timestamp, flagged, location)
        self.save_to_log(timestamp, flagged, location, response)
        
        # delay
        sleep(2)
    def snap_photo(self, t):
        # determine current date/time
        # determine the number of seconds that have elapsed since midnight
        s = t.second + (t.minute * 60) + (t.hour * 60 * 60)
        # use the date/time to generate a unique file name for photos (1/1/2018~21223.png)
        self.camera.capture("/home/pi/Desktop/{0}~{1}.jpg".format(t.strftime("%Y-%m-%d"), s))
        
    def get_json_timestamp(self, t):
        t_json = "{0}-{1}-{2}T{3}:{4}:{5}".format(t.strftime("%Y"), t.strftime("%m"), t.strftime("%d"), t.strftime("%H"), t.strftime("%M"), t.strftime("%S"))
        return t_json
    
    def get_random_location(self):
        return random.randint(1, 3)
        
    def post_event(self, timestamp, flagged, location):
        url = 'https://modas-jsg.azurewebsites.net/api/event/'
        headers = { 'Content-Type': 'application/json'}
        payload = { 'timestamp': self.get_json_timestamp(timestamp), 'flagged': flagged, 'locationId': location }
        print(payload)
        
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        return r.status_code
        
    def save_to_log(self, timestamp, flagged, location, response):
        filename = "{0}-{1}-{2}.log".format(timestamp.strftime("%Y"), timestamp.strftime("%m"), timestamp.strftime("%d"))
        log = self.get_json_timestamp(timestamp) + ',' + str(flagged) + ',' + str(location) + ',' + str(response) + '\n'
        print('writing log: ' + log)
        f = open(filename, "a")
        f.write(log)
        f.close()
        

    def reset(self):
        self.red.off()
        self.green.on()
        
    def toggle(self):
        self.armed = not self.armed
        if self.armed:
            self.arm_system()
        else:
            self.disarm_system()
            
    def arm_system(self):
        print("System armed in 3 seconds")
        self.red.off()
        # enable camera
        self.camera.start_preview()
        # 3 second delay
        self.green.blink(on_time=.25, off_time=.25, n=6, background=False)
        # enable PIR
        self.pir.when_motion = self.init_alert
        self.pir.when_no_motion = self.reset
        self.green.on()
        print("System armed")
        
    def disarm_system(self):
        # disable PIR
        self.pir.when_motion = None
        self.pir.when_no_motion = None
        # disable camera
        self.camera.stop_preview()
        self.red.on()
        self.green.off()
        print("System disarmed")

m = Modas()

try:
    # program loop
    while True:
        sleep(.001)
# detect Ctlr+C
except KeyboardInterrupt:
    if m.armed:
        m.disarm_system()