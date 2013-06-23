from evdev import InputDevice, categorize, ecodes, list_devices, events
from phue import Bridge
import requests
import threading
import time
from select import select
import random
import traceback
import web
import json
import sys

class MousePadHandler(object):
  """Handles mouse pad events to change brightness and hue"""
  #TODO consider splitting bridge-specific commands from logical commands

  max_x = 400
  max_y = 320

  slow_transition = 20 #tenths of a second

  def __init__(self, sender):
    self.sender = sender
    self.reset()

  def reset(self):
    self.tx = self.max_x / 2
    self.ty = self.max_y / 2

  def on(self):
    command = self.append_xy({'on': True, 'transitiontime': self.slow_transition})
    self.sender.set(command)

  def off(self):
    #turning off doesn't necessitate changing hue or brightness, so use a raw command
    command = {'on': False, 'transitiontime': self.slow_transition}
    self.sender.set(command)

  def append_xy(self, base={}):
    hue = int(65000.0 * (float(self.tx) / float(self.max_x)))
    bri = int(255.0 * (float(self.ty) / float(self.max_y)))
    command = {'bri': bri, 'hue': hue, 'sat': 255}

    base.update(command)
    return base

  def move_left(self, amount):
    self.tx = max(0, self.tx + amount)

  def move_right(self, amount):
    self.tx = min(self.max_x, self.tx + amount)

  def move_up(self, amount):
    self.ty = min(self.max_y, self.ty - amount)

  def move_down(self, amount):
    self.ty = max(0, self.ty - amount)

  def update(self):
    command = self.append_xy()

    #echo only every so often...
    if random.randint(1,100) < 5:
      print command

    self.sender.set(command)


class InputDeviceDispatcher(object):
  """Defines a listener for mouse movement events, encoding them into bridge commands"""

  def __init__(self, device, handler):
    self.device = device
    self.handler = handler

  def start(self):
    for event in self.device.read_loop():
      self.handle_event(event)
  
  def handle_event(self, event):
    event = categorize(event)
    if isinstance(event, events.KeyEvent):

      if event.event.code == ecodes.BTN_MOUSE:
        self.handler.reset() #TODO consider not doing this unless double-clicking?
        self.handler.on()

      elif event.event.code == ecodes.BTN_RIGHT:
        self.handler.reset() #TODO consider not doing this at all?
        self.handler.off()

    elif isinstance(event, events.RelEvent):

      if event.event.code == ecodes.REL_X: #left/right movement
        if event.event.value < 0:
          self.handler.move_left(event.event.value)
        elif event.event.value > 0:
          self.handler.move_right(event.event.value)

      elif event.event.code == ecodes.REL_Y: #up/down movement
        if event.event.value > 0:
          self.handler.move_down(event.event.value)
        elif event.event.value < 0:
          self.handler.move_up(event.event.value)

      else:
        print 'other relative event'

      self.handler.update()

class Sender(threading.Thread):
  """Runs a thread that transmits commands to the bridge"""

  def __init__(self, bridge):
    threading.Thread.__init__(self)
    self.daemon = True
    self.bridge = bridge
    self.next = {'hue':32500,'bri': 128, 'sat': 255} #defaults; TODO make configurable?
    self.dirty = True

  def run(self):
    """
    Runs a never-ending loop looking for the dirty flag, 
    sleeping 1/10th of a second between each attempt to send a message
    """
    while (True):
      if self.dirty:
        self.dirty = False
        try:
          #TODO configure somehow?
          self.bridge.set_light([1,2,3], self.next)
          #self.bridge.set_group(1, self.next)
        except Exception, ex:
          print traceback.format_exc() #TODO eat, or notify?
      time.sleep(0.1) #TODO make configurable?
  
  def set(self, next):
    """Sets the command that should be transmitted on the next loop iteration"""
    self.next = next
    self.dirty = True

class WebApp(web.application):
  def run(self, port=8080, *middleware):
    func = self.wsgifunc(*middleware)
    return web.httpserver.runsimple(func, ('0.0.0.0', port))

class Web(threading.Thread):

  def __init__(self, handler):
    threading.Thread.__init__(self)
    self.daemon = True
    Web.handler = handler

  def run(self):
    urls = ('/', 'index')
    WebApp(urls, self.__class__.__dict__).run()

  class index:
    def GET(self):
      return json.dumps(dict(x=Web.handler.tx,y=Web.handler.ty))
    
  class restart:
    def GET(self):
      return 'not yet'

if __name__ == '__main__':

  devices = [InputDevice(x) for x in list_devices()]

  #TODO consider a gentler setup for this to pick a device?
  dev = [d for d in devices if d.name == 'Mouse Pad']

  print 'Detected mouse pad devices: %s' % str(dev)

  if dev and len(dev) > 0:
    #get IP of bridge; TODO consider other ways?
    if len(sys.argv) > 1:
      ip = sys.argv[1]
    else:
      r = requests.get('http://www.meethue.com/api/nupnp')
      d = r.json()
      ip = d[0]['internalipaddress']

    #connect to bridge
    b = Bridge(ip)  

    #this is our device
    dev = dev[0]

    #start the sender
    sender = Sender(b)
    sender.start()

    #create the command handler
    handler = MousePadHandler(sender)

    #start the web handler
    w = Web(handler)
    w.start()

    #start the device loop
    d = InputDeviceDispatcher(dev, handler)
    d.start()
else:
  print 'No devices detected, exiting' #TODO notify and not exit instead?
