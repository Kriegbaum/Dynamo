from DYNAcore import *
import gpiozero as GPIO
from signal import pause

BOUNCE = 0.1

button1 = GPIO.Button(26, bounce_time=BOUNCE)
button2 = GPIO.Button(20, bounce_time=BOUNCE)
button3 = GPIO.Button(19, bounce_time=BOUNCE)
button4 = GPIO.Button(21, bounce_time=BOUNCE)


def run1():
    roomDict['bedroom'].scene(scenes['Natural Glow'], 0.3)

def run2():
    roomDict['bedroom'].scene(scenes['Night'], 0.3)

def run3():
    roomDict['bedroom'].scene(scenes['Void'], 0.3)

def off():
    roomDict['bedroom'].off()


button1.when_pressed = run1
button2.when_pressed = run2
button3.when_pressed = run3
button4.when_pressed = off

pause()
