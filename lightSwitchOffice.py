from Tantallion import *
import gpiozero as GPIO
from signal import pause
import time

button1 = GPIO.Button(19)
button2 = GPIO.Button(16)
button3 = GPIO.Button(26)
button4 = GPIO.Button(20)

iterList = [0,0,0]

naturalLooks = ['Copper', 'Burma', 'Snowy', 'Japanese', 'Sacred', 'Eternity']
saturatedLooks = ['Jelly', 'Vaporwave', 'Intersection', 'Eiffel', 'Valtari', 'Umbrella', 'Void']
contrastLooks = ['Toplight', 'Night', 'Cabinet']

natrualLooks = [scenes[x] for x in naturalLooks]
saturatedLooks = [scenes[x] for x in saturatedLooks]
contrastLooks = [scenes[x] for x in contrastLooks]

def run1():
    controllerDict['officeFC'].setArbitration('ButtonPress')
    roomDict['office'].scene(naturalLooks[iterList[0]])
    iterList[0] += 1
    if iterList[0] > len(naturalLooks) - 1:
        iterList[0] = 0
def run2():
    controllerDict['officeFC'].setArbitration('ButtonPress')
    roomDict['office'].scene(saturatedLooks[iterList[1]])
    iterList[1] += 1
    if iterList[1] > len(saturatedLooks) - 1:
        iterList[1] = 0
def run3():
    controllerDict['officeFC'].setArbitration('ButtonPress')
    roomDict['office'].scene(contrastLooks[iterList[2]])
    iterList[2] += 1
    if iterList[2] > len(contrastLooks) - 1:
        iterList[2] = 0
def run4():
    controllerDict['officeFC'].setArbitration('ButtonPress')
    roomDict['office'].off()

print('Initalizing...')
fixtureDict['Whiteboard'].setColor([0,0,255], 1)
time.sleep(1)
fixtureDict['Whiteboard'].off(1)
time.sleep(1)
fixtureDict['Whiteboard'].setColor([0,0,255], 1)
time.sleep(1)
fixtureDict['Whiteboard'].off(1)

button1.when_pressed = run1
button2.when_pressed = run2
button3.when_pressed = run3
button4.when_pressed = run4

pause()
