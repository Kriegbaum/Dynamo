import sys
sys.path.append('..')

from Tantallion import *

patch = Patch()

patch.relay('left speaker').on()
patch.relay('right speaker').on()
patch.relay('subwoofer').on()
