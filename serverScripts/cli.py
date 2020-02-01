import sys
sys.path.append('..')

from Tantallion import *

patch = Patch()

for c in patch.controllers:
    exec("%s = patch.controller(\'%s\')" % (c, c))

for f in patch.fixtures:
    exec("%s = patch.fixture(\'%s\')" % (f, f))

for r in patch.relays:
    exec("%s = patch.controller(\'%s\')" % (r, r))

for r in patch.rooms:
    exec("%s = patch.controller(\'%s\')" % (r, r))
