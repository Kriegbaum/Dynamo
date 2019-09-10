import sys
sys.path.append('..')

from Tantallion import *
import gpiozero as GPIO
from signal import pause
import multiprocessing
#from strandEffects import *

activeThreads = []
patch = Patch()
room = patch.room('bedroom')

def killEveryone():
    for i in activeThreads:
        activeThreads.pop().terminate()

button1 = GPIO.Button(27)
button2 = GPIO.Button(22)
button3 = GPIO.Button(10)
button4 = GPIO.Button(9)

'''
def sleepFade():
    patch.room('office').off()
    patch.room('living room').off()
    patch.room('kitchen').off()
    room.setColor([0,0,50], 300)
    time.sleep(330)
    room.off(60)
    time.sleep(700)
    patch.room('all').relaysOff()

def vaporCity():
    imagePath = ('/home/pi', 'vapor_city.jpg')
    vapor = multiprocessing.Process(target=web.imageSample, args=imagePath)
    room.off(15)
    vapor.start()
    activeThreads.append(vapor)

def runFlies():
    flies = multiprocessing.Process(target=web.fireflies)
    flies.start()
    activeThreads.append(flies)
'''

def run1():
    killEveryone()
    room.setArbitration('ButtonPress')
    room.scene(patch.scenes['Mountains'])

def run2():
    killEveryone()
    room.setArbitration('ButtonPress')
    room.off()

def run3():
    killEveryone()
    room.relaysOn()

def run4():
    killEveryone()
    room.setArbitration('ButtonPress')
    room.relaysOff()

'''
def runCenterRight():
    killEveryone()
    room.setArbitration('Sleeptime')
    goodnight = multiprocessing.Process(target=sleepFade)
    goodnight.start()
    activeThreads.append(goodnight)

def runCenterLeft():
    killEveryone()
    room.setArbitration('StrandEffect')
    runFlies()

def runLeft():
    killEveryone()
    room.setArbitration('ButtonPress')
    room.scene(scenes['Void'], 1.5)
'''

button1.when_pressed = run1
button2.when_pressed = run2
button3.when_pressed = run3
button4.when_pressed = run4

pause()
