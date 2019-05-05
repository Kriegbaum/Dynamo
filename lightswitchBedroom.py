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


button1.when_pressed = run1
button2.when_pressed = run2
button3.when_pressed = run3
button4.when_pressed = off

pause()
