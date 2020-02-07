import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Tantallion import *
import gpiozero as GPIO
from signal import pause
import multiprocessing


activeThreads = []
patch = Patch()
room = patch.room('living room')

def killEveryone():
    for i in activeThreads:
        activeThreads.pop().terminate()

button1 = GPIO.Button(16)
button2 = GPIO.Button(26)
button3 = GPIO.Button(20)
button4 = GPIO.Button(21)

def stereosOn():
    room.relaysOn()

def stereosOff():
    room.relaysOff()

def run1():
    print('button 1 pressed')
    stereosOn()

def run2():
    print('button 2 pressed')
    stereosOff()

def run3():
    print('button 3 pressed')

def run4():
    print('button 4 pressed')


button1.when_pressed = run1
button2.when_pressed = run2
button3.when_pressed = run3
button4.when_pressed = run4

pause()
