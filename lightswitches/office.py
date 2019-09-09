import sys
sys.path.append('..')

from Tantallion import *
import gpiozero as GPIO
from signal import pause
import time

patch = Patch()
room = patch.room('office')


button1 = GPIO.Button(19, bounce_time=0.01)
button2 = GPIO.Button(16, bounce_time=0.01)
button3 = GPIO.Button(26, bounce_time=0.01)
button4 = GPIO.Button(20, bounce_time=0.01)

frankenstein = GPIO.Button(13)

iterList = [0,0,0]

naturalLooks = ['Copper', 'Burma', 'Snowy', 'Japanese', 'Sacred', 'Eternity']
saturatedLooks = ['Jelly', 'Vaporwave', 'Intersection', 'Eiffel', 'Valtari', 'Umbrella', 'Void']
contrastLooks = ['Toplight', 'Night', 'Cabinet']

naturalLooks = [scenes[x] for x in naturalLooks]
saturatedLooks = [scenes[x] for x in saturatedLooks]
contrastLooks = [scenes[x] for x in contrastLooks]

def run1():
    room.setArbitration('ButtonPress')
    room.scene(naturalLooks[iterList[0]], .3)
    iterList[0] += 1
    if iterList[0] >= len(naturalLooks):
        iterList[0] = 0
def run2():
    room.setArbitration('ButtonPress')
    room.scene(saturatedLooks[iterList[1]], .3)
    iterList[1] += 1
    if iterList[1] >= len(saturatedLooks):
        iterList[1] = 0
def run3():
    room.setArbitration('ButtonPress')
    room.scene(contrastLooks[iterList[2]], .3)
    iterList[2] += 1
    if iterList[2] >= len(contrastLooks) :
        iterList[2] = 0
def run4():
    room.setArbitration('ButtonPress')
    room.off()

def periphOn():
    room.relaysOn()

def periphOff():
    room.relaysOff()

print('Initalizing...')
patch.fixture('Whiteboard').setColor([0,0,255], .5)
time.sleep(.5)
patch.fixture('Whiteboard').off(.5)
time.sleep(.5)
patch.fixture('Whiteboard').setColor([0,0,255], .5)
time.sleep(.5)
patch.fixture('Whiteboard').off(.5)

button1.when_pressed = run1
button2.when_pressed = run2
button3.when_pressed = run3
button4.when_pressed = run4

frankenstein.when_pressed = periphOn
frankenstein.when_released = periphOff

pause()
