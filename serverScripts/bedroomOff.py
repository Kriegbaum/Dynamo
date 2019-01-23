import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from DYNAcore import *

room = rooms['bedroom']
setArbitration(False, 'bedroomFC')
multiCommandList = []

for l in room:
    if l.system == 'Fadecandy':
        color = [0,0,0]
        multiCommandList.append([l, color, .5])

    elif l.system == 'Hue':
        command = {'on': False, 'transitiontime': 5}
        bridge.set_light(l.id, command)

    else:
        print('You fucked up and now there is an improperly classed Fixture in your room!')
        print(l.name)
        print(l.system)

sendMultiCommand(multiCommandList)
