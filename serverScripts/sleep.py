import sys
sys.path.append('..')

from Tantallion import *
import os
import time
import subprocess
from random import shuffle
import platform


if platform.system() == 'Windows':
    from cuepy import CorsairSDK
    import musicbeeipc
    subprocess.Popen("C:\\Program Files (x86)\\MSI\\MSI LED Tool.exe")

    time.sleep(1)
    os.system('taskkill /IM \"MSI LED Tool.exe\" /F')

    cue = CorsairSDK('E:\\code\\CUESDK\\bin\\x64\\CUESDK.x64_2013.dll')
    keyboard = cue.device(0)
    for i in range(121):
        keyboard.set_led(i, [0,0,0])

    patch = Patch()
    mb = musicbeeipc.MusicBeeIPC()
    web = patch.fixture('bedroom array')
    os.system('E:\\nircmd\\nircmd.exe setsysvolume 10000')
    mb.set_volume(100)
    def volumeDown():
        vol = 100
        for i in range(65):
            mb.set_volume(vol)
            vol -= 1
            time.sleep(7)

    os.system('E:\\nircmd\\nircmd.exe monitor off')

    #patch.rooms['bedroom'].setArbitration('SleepTime')
    patch.controller('bedroomFC').setArbitration('SleepTime')
    time.sleep(20)

    #patch.rooms['bedroom'].setColor([15,12,85], fadeTime=95)
    patch.fixture('dresser').setColor([15,12,85], fadeTime=95)
    patch.fixture('worklight').setColor([15,12,85], fadeTime=95)
    patch.fixture('spidergod').setColor([15,12,85], fadeTime=95)
    patch.fixture('whiteboard').setColor([15,12,85], fadeTime=95)
    patch.fixture('bedroom array').setColor([15,12,85], fadeTime=95)

    patch.fixture('spidergod').setColor([255,0,0], fadeTime=95)
    patch.fixture('desk').off()
    time.sleep(105)
    patch.fixture('dresser').off(45)
    patch.fixture('worklight').off(45)
    patch.fixture('spidergod').off(60)
    patch.fixture('whiteboard').off(60)
    patch.fixture('bedroom array').rollFade([15, 12, 75], 120)
    randPix = web.indexes.copy()
    shuffle(randPix)
    volDown = threading.Thread(target=volumeDown)
    volDown.start()
    whiteVal = 90
    for i in randPix:
        flyThread = threading.Thread(target=web.firefly, args=[i, [whiteVal,whiteVal,whiteVal], [whiteVal / 4,whiteVal / 4,whiteVal / 4], [0,12,22], 0.8])
        flyThread.start()
        time.sleep(1.5 * randomPercent(70, 155))
    shuffle(randPix)
    for i in randPix:
        flyThread = threading.Thread(target=web.firefly, args=[i, [85,117,0], [10,26,0], [0,0,0], 0.8])
        flyThread.start()
        time.sleep(1.5 * randomPercent(70, 155))
        whiteVal -= 0.1
    time.sleep(10)

    while mb.get_play_state_str() != 'Stopped':
        time.sleep(1)

    patch.rooms['bedroom'].relaysOff()
    mb.set_volume(100)
    os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')

elif platform.system() == 'Linux':
    '''
    subprocess.Popen("C:\\Program Files (x86)\\MSI\\MSI LED Tool.exe")
    #TODO: Linux implementation of GPU KILL
    time.sleep(1)
    os.system('taskkill /IM \"MSI LED Tool.exe\" /F')
    '''

    os.system('ckb-next --mode "Off"')

    patch = Patch()

    web = patch.fixture('bedroom array')

    patch.relay('left monitor').off()
    time.sleep(1)
    patch.relay('right monitor').off()
    time.sleep(1)
    patch.relay('center monitor').off()

    patch.rooms['bedroom'].setArbitration('SleepTime')
    time.sleep(10)
    patch.rooms['bedroom'].setColor([15,12,85], fadeTime=95)
    patch.fixture('desk').off(90)
    patch.fixture('dresser').off(90)
    time.sleep(105)
    patch.fixture('worklight').off(45)
    randPix = web.indexes.copy()
    shuffle(randPix)
    for i in randPix:
        flyThread = threading.Thread(target=web.firefly, args=[i, [90,90,90], [20,20,20], [0,0,0], 0.8])
        flyThread.start()
        time.sleep(1.5 * randomPercent(70, 155))
    time.sleep(2)

    while subprocess.check_output('banshee --query-current-state', shell=True) == b'current-state: playing\n':
        time.sleep(3)

    patch.rooms['bedroom'].relaysOff()
    os.system('pm-suspend')
