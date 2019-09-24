import sys
sys.path.append('..')

from Tantallion import *
import os
import musicbeeipc
import time
from cuepy import CorsairSDK
import subprocess

subprocess.Popen("C:\\Program Files (x86)\\MSI\\MSI LED Tool.exe")
time.sleep(1)
os.system('taskkill /IM \"MSI LED Tool.exe\" /F')

cue = CorsairSDK('E:\\code\\CUESDK\\bin\\x64\\CUESDK.x64_2013.dll')
keyboard = cue.device(0)
for i in range(121):
    keyboard.set_led(i, [0,0,0])

patch = Patch()
mb = musicbeeipc.MusicBeeIPC()

os.system('E:\\nircmd\\nircmd.exe monitor off')

patch.rooms['bedroom'].setColor([6,0,64], fadeTime=45)
time.sleep(90)
patch.rooms['bedroom'].off(45)

while mb.get_play_state_str() != 'Stopped':
    time.sleep(1)

patch.rooms['bedroom'].relaysOff()
#os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
