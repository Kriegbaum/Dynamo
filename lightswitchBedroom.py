import gpiozero as GPIO
from signal import pause
import multiprocessing
from strandEffects import *

activeThreads = []
patch = Patch()
room = patch.room('bedroom')

def killEveryone():
    for i in activeThreads:
        activeThreads.pop().terminate()

button1 = GPIO.Button(26)
button2 = GPIO.Button(20)
button3 = GPIO.Button(19)
button4 = GPIO.Button(21)

left = GPIO.Button(12)
centerLeft = GPIO.Button(13)
centerRight = GPIO.Button(5)
right = GPIO.Button(6)

def sleepFade():
    room.setColor([0,0,50], 300)
    time.sleep(330)
    room.off(60)


def runFlies():
    flies = multiprocessing.Process(target=fireflies)
    flies.start()
    activeThreads.append(flies)

def run1():
    killEveryone()
    room.setArbitration('ButtonPress')
    room.scene(scenes['Natural Glow'], 1.1)

def run2():
    killEveryone()
    room.setArbitration('ButtonPress')
    room.scene(scenes['Night'], 1.1)

def run3():
    killEveryone()
    room.setArbitration('StrandEffect')
    runFlies()

def off():
    killEveryone()
    room.setArbitration('ButtonPress')
    room.off()

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


button1.when_pressed = run1
button2.when_pressed = run2
button3.when_pressed = run3
button4.when_pressed = off

left.when_pressed = runLeft
centerLeft.when_pressed = runCenterLeft
centerRight.when_pressed = runCenterRight
right.when_pressed = off

pause()
