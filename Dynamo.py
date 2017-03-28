import opc
import os
from phue import Bridge

def serverkill():
#Shuts down server binary, registered in server start as atexit function
    os.system('TASKKIILL /F /IM fcserver.exe')

def serverstart():
#Initialize Fadecandy server support
    #Make sure server and script are coterminal
    atexit.register(serverkill)
    #Run fadecandy server binary in background
    os.system('START /B E:\\Code\\fadecandy\\bin\\fcserver.exe')
    FCclient = opc.Client('localhost:7890')
    #FC control object. 512 RGB pixels, split into eight 64 pixel groups
    global FCpixels = [ [0,0,0] ] * 512

    #Window trim top HARDCODED
    global s1 = range(0,128)
    #Window trim bottom HARDCODED
    global s2 = range(129,192)
    #Computer internal light
    global s3 = range(192,256)


bridge = Bridge('10.0.10')
bedroom = [7,8,10,11,17,15,s1,s2]
living_room = [1,2,3,4,5,6,12,13]

global_sat = 1
global_bri = 1
global_speed = 1
