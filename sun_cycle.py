from phue import Bridge
import datetime
import opc
import atexit
import os
import time
import math
import astral

#Establish FC objects
def serverkill():
    os.system('TASKKILL /F /IM fcserver.exe')
atexit.register(serverkill)
os.system('START /B E:\\Code\\fadecandy\\bin\\fcserver.exe')
FCclient = opc.Client('localhost:7890')
FCpixels = [ [0, 0, 0] ] * 512

s1 = range(0, 128)
s2 = range(129, 192)
s3 = range(192, 256)
#End FC objects

#Establish hue objects
bridge = Bridge('10.0.10')
bedroom = [7,8,10,11,17,15,s1,s2]
living_room = [1,2,3,4,5,6,12,13]
#End Hue objects

#astral objects
city_name = 'chicago'
a = Astral()
city = a[city_name]
sun = city.sun(date=datetime.date.today(), local=True)
