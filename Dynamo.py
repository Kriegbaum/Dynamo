import opc
import time
import os
import atexit
from phue import Bridge

def serverkill():
#Shuts down server binary, registered in server start as atexit function
    os.system('TASKKILL /F /IM fcserver.exe')

def serverstart():
#Initialize Fadecandy server support
    #Make sure server and script are coterminal
    atexit.register(serverkill)
    #Run fadecandy server binary in background
    os.system('START /B E:\\Code\\fadecandy\\bin\\fcserver.exe')
    time.sleep(0.3)

FCclient = opc.Client('localhost:7890')

#FC control object. 512 RGB pixels, split into eight 64 pixel groups
FCpixels = [ [0,0,0] ] * 512

#Window trim top HARDCODED
s1 = range(0,128)
#Window trim bottom HARDCODED
s2 = range(128,192)
#Computer internal light
s3 = range(192,256)




bridge = Bridge('10.0.0.10')
bedroom = [7,8,10,11,17,18,s1,s2,s3]
living_room = [1,2,3,4,5,6,12,13]
dining_room = [18]

room_dict = {'bedroom': bedroom, 'living room': living_room, 'dining room': dining_room}
