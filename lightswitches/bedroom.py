import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Tantallion import *
import gpiozero as GPIO
from signal import pause
import multiprocessing

imageWarm = True
activeThreads = []
patch = Patch()
room = patch.room('bedroom')
web = patch.fixture('bedroom array')

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
    patch.fixture('dresser').setColor([141, 24, 131])
    vapor.start()
    activeThreads.append(vapor)

def eiffel():
    imagePath = ('/home/pi', 'eiffel4.jpg')
    eiffel3 = multiprocessing.Process(target=web.imageSample, args=imagePath)
    patch.fixture('desk').setColor([150, 105, 50])
    patch.fixture('dresser').setColor([78, 52, 37])
    patch.fixture('worklight').setColor([120, 85, 65])
    eiffel3.start()
    activeThreads.append(eiffel3)

def runFlies():
    flies = multiprocessing.Process(target=web.fireflies)
    flies.start()
    activeThreads.append(flies)

def run1():
    print('button 1 pressed')
    killEveryone()
    room.setArbitration('ButtonPress')
    if imageWarm:
        imageWarm = False
        eiffel()
    else:
        imageWarm = True
        vaporCity()

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
