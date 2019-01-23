import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from DYNAcore import *


bridge.set_light(22, 'on', True)
time.sleep(1)
bridge.set_light(29, 'on', True)
time.sleep(1)
bridge.set_light(28, 'on', True)
time.sleep(1)
bridge.set_light(17, 'on', True)
bridge.set_light(21, 'on', True)
bridge.set_light(18, 'on', True)
