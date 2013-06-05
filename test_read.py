from asyncore import file_dispatcher, loop
from evdev import InputDevice, categorize, ecodes
dev = InputDevice('/dev/input/event1')

class InputDeviceDispatcher(file_dispatcher):
  def __init__(self, device):
    self.device = device
    file_dispatcher.__init__(self, device)
  
  def recv(self, ign=None):
    return self.device.read()

  def handle_read(self):
    for event in self.recv():
      print(categorize(event))

InputDeviceDispatcher(dev)
loop()