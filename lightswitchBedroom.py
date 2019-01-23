from DYNAcore import *
import gpiozero as GPIO
from signal import pause

button1 = GPIO.Button(26)
button2 = GPIO.Button(20)
button3 = GPIO.Button(19)
button4 = GPIO.Button(21)


room = rooms['bedroom grouped']
roomController = 'bedroomFC'

LowLight = {
             'Full Array'      : grbFix([10, 0, 50]),
	        'Bedroom Closet'  : [10, 10, 0],
	        'Window'          : [255, 150, 100]
	   }

Standard = {
            'Full Array'      : grbFix([195, 150, 99]),
            'Bedroom Closet'  : [0,0,0],
            'Window'          : [0,0,0]}

StreetLight = {
            'Full Array'      : [0,0,0],
	        'Bedroom Closet'  : [0, 0, 0],
	        'Window'          : [255, 185, 140]
	   }


def makeLight(look):
    setArbitration(False, roomController)
    multiCommandList = []
    for l in room:
        if l.system == 'Fadecandy':
            color = colorCorrect(l, look[l.name])
            multiCommandList.append([l, color, .5])

        elif l.system == 'Hue':
            if look[l.name] == [0,0,0]:
                command = {'on' : False}
            else:
                color = convert(colorCorrect(l, look[l.name]))
                command = {'hue': color[0], 'sat': color[1], 'bri': color[2], 'on': True, 'transitiontime': 5}
            bridge.set_light(l.id, command)

        else:
            print('You fucked up and now there is an improperly classed Fixture in your room!')
            print(l.name)
            print(l.system)
    sendMultiCommand(multiCommandList)

def run1():
    makeLight(Standard)

def run2():
    makeLight(LowLight)

def run3():
    makeLight(StreetLight)

def off():
    setArbitration(False, roomController)
    multiCommandList = []
    for l in room:
        if l.system == 'Hue':
            bridge.set_light(l.id, 'on', False)
        if l.system == 'Fadecandy':
            multiCommandList.append([l, [0,0,0], 0.5])
    sendMultiCommand(multiCommandList)


button1.when_pressed = run1
button2.when_pressed = run2
button3.when_pressed = run3
button4.when_pressed = off

pause()
