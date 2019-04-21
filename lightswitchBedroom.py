from Tantallion import *
import gpiozero as GPIO
from signal import pause


button1 = GPIO.Button(26)
button2 = GPIO.Button(20)
button3 = GPIO.Button(19)
button4 = GPIO.Button(21)


def run1():
    roomDict['bedroom'].scene(scenes['Natural Glow'], 1.1)

def run2():
    roomDict['bedroom'].scene(scenes['Night'], 1.1)

def run3():
    roomDict['bedroom'].scene(scenes['Void'], 1.1)

def off():
    roomDict['bedroom'].off()


button1.when_pressed = run1
button2.when_pressed = run2
button3.when_pressed = run3
button4.when_pressed = off

pause()
