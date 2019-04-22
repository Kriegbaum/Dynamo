from Tantallion import *
import gpiozero as GPIO
from signal import pause

patch = Patch()
room = patch.room('bedroom')

button1 = GPIO.Button(26)
button2 = GPIO.Button(20)
button3 = GPIO.Button(19)
button4 = GPIO.Button(21)


def run1():
    room.setArbitration('ButtonPress')
    room.scene(scenes['Natural Glow'], 1.1)

def run2():
    room.setArbitration('ButtonPress')
    room.scene(scenes['Night'], 1.1)

def run3():
    room.setArbitration('ButtonPress')
    room.scene(scenes['Void'], 1.1)

def off():
    room.off()


button1.when_pressed = run1
button2.when_pressed = run2
button3.when_pressed = run3
button4.when_pressed = off

pause()
