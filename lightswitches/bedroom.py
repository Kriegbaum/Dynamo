import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Tantallion import *
import gpiozero as GPIO
from signal import pause
import multiprocessing

warm = True
activeThreads = []
patch = Patch()
room = patch.room('bedroom')
web = patch.fixture('bedroom array')
class imageIterator:
    def __init__(self):
        self.it = 0
image = imageIterator()

def killEveryone():
    for i in activeThreads:
        activeThreads.pop().terminate()

button1 = GPIO.Button(27)
button2 = GPIO.Button(22)
button3 = GPIO.Button(10)
button4 = GPIO.Button(9)


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
    imagePath = ('/home/pi', 'vapor_city2.jpg')
    vapor = multiprocessing.Process(target=web.imageSample, args=imagePath)
    patch.fixture('worklight').setColor([128, 20, 50])
    patch.fixture('desk').setColor([3, 15, 149])
    patch.fixture('dresser').setColor([211, 36, 196])
    vapor.start()
    activeThreads.append(vapor)

def eiffel():
    imagePath = ('/home/pi', 'eiffel4.jpg')
    eiffel3 = multiprocessing.Process(target=web.imageSample, args=imagePath)
    patch.fixture('desk').setColor([150, 105, 50])
    patch.fixture('dresser').setColor([175, 117, 82])
    patch.fixture('worklight').setColor([120, 85, 65])
    eiffel3.start()
    activeThreads.append(eiffel3)

def snowy():
    imagePath = ('/home/pi', 'snowy-dim.jpg')
    snow = multiprocessing.Process(target=web.imageSample, args=imagePath)
    patch.fixture('worklight').setColor([128,128,128])
    patch.fixture('desk').setColor([128,128,128])
    patch.fixture('dresser').setColor([128,128,128])
    snow.start()
    activeThreads.append(snow)

def valtari():
    imagePath = ('/home/pi', 'valtari2.jpg')
    valtari = multiprocessing.Process(target=web.imageSample, args=imagePath)
    patch.fixture('worklight').setColor([228,208,70])
    patch.fixture('desk').setColor([52,61,52])
    patch.fixture('dresser').setColor([71,96,22])
    valtari.start()
    activeThreads.append(valtari)

def runFlies():
    flies = multiprocessing.Process(target=web.fireflies)
    flies.start()
    activeThreads.append(flies)

def iteratorTracker(i):
    if i.it == 0:
        i.it += 1
        vaporCity()
    elif i.it == 1:
        i.it += 1
        eiffel()
    elif i.it == 2:
        i.it += 1
        snowy()
    elif i.it == 3:
        i.it = 0
        valtari()

def run1():
    print('button 1 pressed')
    killEveryone()
    room.setArbitration('ButtonPress')
    iteratorTracker(image)

def run2():
    print('button 2 pressed')
    killEveryone()
    room.setArbitration('ButtonPress')
    room.off()

def run3():
    print('button 3 pressed')
    room.relaysOn()

def run4():
    print('button 4 pressed')
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
