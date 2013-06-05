from asyncore import file_dispatcher, loop
from evdev import InputDevice, categorize, ecodes, list_devices, events

devices = [InputDevice(x) for x in list_devices()]
dev = [d for d in devices if d.name == 'Mouse Pad']

class InputDeviceDispatcher(file_dispatcher):
  def __init__(self, device):
    self.device = device
    self.tx = 200
    self.ty = 160
    file_dispatcher.__init__(self, device)
  
  def recv(self, ign=None):
    return self.device.read()

  def handle_read(self):
    for event in self.recv():
      event = categorize(event)
      if isinstance(event, events.RelEvent):
        if event.event.code == ecodes.REL_X:
          if event.event.value < 0:
            self.tx = max(0, self.tx + event.event.value)
          elif event.event.value > 0:
            self.tx = min(400, self.tx + event.event.value)

          print 'X: %d\t\t\t\tPos: (%d, %d)' % (event.event.value, self.tx, self.ty)
        elif event.event.code == ecodes.REL_Y:
          if event.event.value > 0:
            self.ty = max(0, self.ty - event.event.value)
          elif event.event.value < 0:
            self.ty = min(320, self.ty - event.event.value)

          print '\t\tY: %d\t\tPos: (%d, %d)' % (event.event.value, self.tx, self.ty)
        else:
          print 'other relative event'
      #if event.type == ecodes.REL_Y:
      #  print "Y: %d" % event.value
      #elif event.type == ecodes.REL_Y:
      #  print "\t\tX: %d" % event.value
      #print(categorize(event))

print dev

if dev and len(dev) > 0:
  dev = dev[0]
	
  InputDeviceDispatcher(dev)
  loop()
