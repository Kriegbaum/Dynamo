from DYNAcore import *

room = rooms['bedroom']
setArbitration(False, 'bedroomFC')
multiCommandList = []

for l in room:
    if l.system == 'Fadecandy':
        color = [195, 150, 99]
        multiCommandList.append([l, color, .5])

    elif l.system == 'Hue':
        color = convert([195, 150, 99])
        command = {'hue': color[0], 'sat': color[1], 'bri': color[2], 'on': True, 'transitiontime': 5}
        bridge.set_light(l.id, command)

    else:
        print('You fucked up and now there is an improperly classed Fixture in your room!')
        print(l.name)
        print(l.system)

sendMultiCommand(multiCommandList)
