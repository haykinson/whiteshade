from asyncore import file_dispatcher, loop
from evdev import InputDevice, categorize, ecodes, list_devices

devices = [InputDevice(x) for x in list_devices()]
dev = [d for d in devices if d.name == 'Mouse Pad']

class InputDeviceDispatcher(file_dispatcher):
  def __init__(self, device):
    self.device = device
    file_dispatcher.__init__(self, device)
  
  def recv(self, ign=None):
    return self.device.read()

  def handle_read(self):
    for event in self.recv():
      print(categorize(event))

if dev:
	if len(dev) > 1:
		dev = dev[0]
	
	InputDeviceDispatcher(dev)
	loop()