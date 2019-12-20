import sys
sys.path.append('..')

from Tantallion import *

patch = Patch()

patch.relay('left speaker').off()
patch.relay('right speaker').off()
patch.relay('subwoofer').off()
