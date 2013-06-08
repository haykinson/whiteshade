from evdev import InputDevice, categorize, ecodes, list_devices, events
from phue import Bridge
import requests
import threading
import time
from select import select
import random
import traceback

devices = [InputDevice(x) for x in list_devices()]
dev = [d for d in devices if d.name == 'Mouse Pad']

class InputDeviceDispatcher(object):
  def __init__(self, device, sender):
    self.device = device
    self.sender = sender
    self.tx = 200
    self.ty = 160

  #def read_loop(self):
  #  while True:
  #    r,w,x = select([self.device.fd], [], []) #, 1) #1 sec timeout
  #    for event in self.device.read():
  #      yield event

  def start(self):
    for event in self.device.read_loop():
      self.handle_event(event)
  
  def handle_event(self, event):
    event = categorize(event)
    if isinstance(event, events.KeyEvent):
      if event.event.code == ecodes.BTN_MOUSE:
        #turn on, and to normal brightness
        self.tx = 200
        self.ty = 160
        self.sender.set({'on':True,'bri':128,'hue':32500,'transitiontime':20})
      elif event.event.code == ecodes.BTN_RIGHT:
        self.tx = 200
        self.ty = 160
        self.sender.set({'on':False, 'transitiontime': 20})
    elif isinstance(event, events.RelEvent):
      if event.event.code == ecodes.REL_X:
        if event.event.value < 0:
          self.tx = max(0, self.tx + event.event.value)
        elif event.event.value > 0:
          self.tx = min(400, self.tx + event.event.value)
          
        #print 'X: %d\t\t\t\tPos: (%d, %d)' % (event.event.value, self.tx, self.ty)
      elif event.event.code == ecodes.REL_Y:
        if event.event.value > 0:
          self.ty = max(0, self.ty - event.event.value)
        elif event.event.value < 0:
          self.ty = min(320, self.ty - event.event.value)

        #print '\t\tY: %d\t\tPos: (%d, %d)' % (event.event.value, self.tx, self.ty)
      else:
        print 'other relative event'

      hue = int(65000.0 * (float(self.tx) / 400.0))
      bri = int(255.0 * (float(self.ty) / 320.0))
      command = {'bri': bri, 'hue': hue, 'sat': 255}
      #echo only every so often...
      if random.randint() < 5:
        print command

      self.sender.set(command)

class Sender(threading.Thread):
  def __init__(self, bridge):
    threading.Thread.__init__(self)
    self.daemon = True
    self.bridge = bridge
    self.next = {'hue':32500,'bri': 128, 'sat': 255}
    self.dirty = True

  def run(self):
    while (True):
      if self.dirty:
        self.dirty = False
        try:
          self.bridge.set_light([1,2,3], self.next)
          #self.bridge.set_group(1, self.next)
        except Exception, ex:
          print traceback.format_exc()
      time.sleep(0.1)
  
  def set(self, next):
    self.next = next
    self.dirty = True

print dev

if dev and len(dev) > 0:
  r = requests.get('http://www.meethue.com/api/nupnp')
  d = r.json()
  ip = d[0]['internalipaddress']

  b = Bridge(ip)  

  dev = dev[0]

  sender = Sender(b)
  sender.start()

  d = InputDeviceDispatcher(dev, sender)
  d.start()

