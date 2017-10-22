import RPi.GPIO as GPIO
import time
from phue import Bridge
import opc
import colorsys


###########RPI pins defined
GPIO.setmode(GPIO.BCM)

#Top left button (1)
GPIO.setup(19, GPIO.IN)
#Top right button (2)
GPIO.setup(16, GPIO.IN)
#Bottom left button (3)
GPIO.setup(26, GPIO.IN)
#Bottom right button (4)
GPIO.setup(20, GPIO.IN)

#Red
GPIO.setup(22, GPIO.OUT)
#Green
GPIO.setup(23, GPIO.OUT)
#Blue
GPIO.setup(24, GPIO.OUT)

###### Lighting Control Objects

#Hue system control object
bridge = Bridge('192.168.1.31')

#OPC go-between that talks to FCserver
FCclient = opc.Client('192.168.1.145:7890')

#FC control object. 512 RGB pixels, split into eight 64 pixel groups
FCpixels = [ [0,0,0] ] * 512

class Fixture:
    def __init__(self, system, name):
        self.system = system
        self.name = name
        self.indexrange = range(0,0)
        self.colorCorrection = [1, 1, 1]
        self.id = 0
        self.grb = True

##### FIXTURE DEFINITIONS

#Fadecandy Fixtures
s1 = Fixture('Fadecandy', 'Windows')
s1.indexrange = range(0,128)
s1.colorCorrection = [1,.8627,.6705]

s3 = Fixture('Fadecandy', 'Fan')
s3.indexrange = range(448,450)
s3.colorCorrection = [1, .91, 0.70588]

s4 = Fixture('Fadecandy', 'Worklight')
s4.indexrange = range(384,385)
s4.colorCorrection = [1, .97777, 0.63137]

#Hue Fixtures
h10 = Fixture('Hue', 'Duct')
h10.id = 10

h11 = Fixture('Hue', 'Skull')
h11.id = 11
h11.colorCorrection= [.92,.95,1]

h17 = Fixture('Hue', 'Floor Lamp')
h17.id = 17

h18 = Fixture('Hue', 'Corner')
h18.id = 18

room = [h10,h11,h17,h18,s1,s3,s4]
#Function Objects
saturated_iteration = 0
natural_iteration = 0
contrast_iteration = 0

#Spidergod aint no fuckboi

#Natural looks

Copper = {
            'Worklight'     : [88,83,87],
            'Fan'           : [139,68,4],
            'Windows'       : [83,87,99],
            'Floor Lamp'    : [37,22,15],
            'Duct'          : [122,106,106],
            'Skull'         : [212,146,70],
            'Corner'        : [144,110,85]
            }

Burma = {
            'Windows'       : [134,89,32],
            'Skull'         : [209,193,169],
            'Worklight'     : [161,116,51],
            'Fan'           : [199,164,96],
            'Corner'        : [177,137,75],
            'Floor Lamp'    : [118,73,16],
            'Duct'          : [168,127,65]
            }

Snowy = {
            'Fan'           : [152,150,151],
            'Windows'       : [219,214,220],
            'Duct'          : [120,114,116],
            'Worklight'     : [114,112,115],
            'Floor Lamp'    : [84,87,94],
            'Skull'         : [172,173,188],
            'Corner'        : [106,90,93]
            }

Japanese = {
            'Windows'       : [123,141,109],
            'Worklight'     : [198,152,68],
            'Corner'        : [195,145,82],
            'Floor Lamp'    : [216,208,189],
            'Duct'          : [224,174,175],
            'Fan'           : [196,171,119],
            'Skull'         : [205,221,200]
            }

Sacred = {
            'Windows'       : [35,178,220],
            'Corner'        : [100,49,25],
            'Duct'          : [81,46,14],
            'Fan'           : [79,60,25],
            'Floor Lamp'    : [85,49,15],
            'Worklight'     : [81,42,9],
            'Skull'         : [44,42,69]
            }

Eternity = {
            'Skull'         : [224,182,165],
            'Worklight'     : [225,205,162],
            'Corner'        : [178,110,107],
            'Windows'       : [223,120,101],
            'Fan'           : [174,112,101],
            'Floor Lamp'    : [144,94,97],
            'Duct'          : [128,85,92]
            }
#Saturated looks

Jelly = {
            'Floor Lamp'    : [0,35,111],
            'Duct'          : [239,30,0],
            'Corner'        : [1,98,175],
            'Windows'       : [254,138,1],
            'Fan'           : [0,0,255],
            'Skull'         : [95,45,0],
            'Worklight'     : [0,174,198]
            }


Valtari = {
            'Skull'         : [125,124,67],
            'Floor Lamp'    : [177,150,81],
            'Corner'        : [145,131,66],
            'Windows'       : [93,92,46],
            'Fan'           : [85,85,33],
            'Worklight'     : [110,98,60],
            'Duct'         : [130,116,65]
            }

Vaporwave = {
            'Worklight'     : [120,200,164],
            'Windows'       : [188,110,241],
            'Skull'         : [117,35,150],
            'Fan'           : [96,71,126],
            'Corner'        : [70,200,135],
            'Duct'          : [129,31,142],
            'Floor Lamp'    : [120,168,146]
            }

Intersection = {
            'Skull'         : [219,118,175],
            'Floor Lamp'    : [135,88,202],
            'Corner'        : [207,112,204],
            'Windows'       : [208,89,153],
            'Fan'           : [75,40,190],
            'Duct'          : [80,47,150],
            'Worklight'     : [79,39,73]
            }

Eiffel = {
            'Fan'           : [255,197,63],
            'Skull'         : [99,52,11],
            'Worklight'     : [128,72,0],
            'Corner'        : [123,50,0],
            'Windows'       : [119,62,7],
            'Duct'          : [112,64,0],
            'Floor Lamp'    : [87,43,8]
            }

Umbrella = {
            'Worklight'     : [43,133,162],
            'Skull'         : [24,100,144],
            'Fan'           : [255,255,255],
            'Corner'        : [26,120,144],
            'Floor Lamp'    : [165,64,107],
            'Duct'          : [7,75,138],
            'Windows'       : [165,64,107]
            }

Toplight = {
            'Worklight'     : [0,0,0],
            'Skull'         : [0,0,0],
            'Fan'           : [30,100,220],
            'Corner'        : [0,0,0],
            'Floor Lamp'    : [0,0,0],
            'Duct'          : [0,0,0],
            'Windows'       : [0,0,0]
            }

Blinds = {
            'Worklight'     : [0,0,0],
            'Skull'         : [0,0,0],
            'Fan'           : [0,0,0],
            'Corner'        : [0,0,0],
            'Floor Lamp'    : [0,0,0],
            'Duct'          : [0,0,0],
            'Windows'       : [255,197,110]
            }

naturalLooks = [Copper, Burma, Snowy, Japanese, Sacred, Eternity]
saturatedLooks = [Jelly, Vaporwave, Intersection, Eiffel, Valtari, Umbrella]
contrastLooks = [Toplight, Blinds]

def convert(RGB):                                                               #Takes RGB value and delivers the flavor of HSV that the hue api uses
    R = RGB[0] / 255                                                            #colorsys takes values between 0 and 1, PIL delivers between 0 and 255
    G = RGB[1] / 255
    B = RGB[2] / 255
    hsv = colorsys.rgb_to_hsv(R, G, B)                                          #Makes standard HSV
    hsv_p = [int(hsv[0] * 360 * 181.33), int(hsv[1] * 255), int(hsv[2] * 255)]  #Converts to Hue api HSV
    return hsv_p

def colorCorrect(fixture, rgb):
    tempList =  [fixture.colorCorrection[0] * rgb[0],
                fixture.colorCorrection[1] * rgb[1],
                fixture.colorCorrection[2] * rgb[2]]
    return tempList

def makeLight(look):
    FCclient.put_pixels(FCpixels)
    for l in room:
        if l.system == 'Fadecandy':
            color = colorCorrect(l, look[l.name])
            for p in l.indexrange:
                FCpixels[p] = color

        elif l.system == 'Hue':
            if look[l.name] == [0,0,0]:
                command - {'on' : False}
            else:
                color = convert(colorCorrect(l, look[l.name]))
                command = {'hue': color[0], 'sat': color[1], 'bri': color[2], 'on': True, 'transitiontime': 7}
            bridge.set_light(l.id, command)

        else:
            print('You fucked up and now there is an improperly classed Fixture in your room!')
            print(l.name)
            print(l.system)

    FCclient.put_pixels(FCpixels)

def off():
    for l in room:
        if l.system == 'Hue':
            bridge.set_light(l.id, 'on', False)
        bridge.set_light(24, 'on', False)
        FCpixels = [ [0,0,0] ] * 512
        FCclient.put_pixels(FCpixels)
        FCclient.put_pixels(FCpixels)

for i in range(0,128):
    FCpixels[i] = [255,0,0]
FCclient.put_pixels(FCpixels)
time.sleep(.5)

for i in range(0,128):
    FCpixels[i] = [255,128,0]
FCclient.put_pixels(FCpixels)
time.sleep(.5)

for i in range(0,128):
    FCpixels[i] = [255,255,0]
FCclient.put_pixels(FCpixels)
time.sleep(.5)

for i in range(0,128):
    FCpixels[i] = [0,255,0]
FCclient.put_pixels(FCpixels)
time.sleep(.5)

for i in range(0,128):
    FCpixels[i] = [0,0,255]
FCclient.put_pixels(FCpixels)
time.sleep(.5)

for i in range(0,128):
    FCpixels[i] = [255,0,255]
FCclient.put_pixels(FCpixels)
time.sleep(.5)

FCpixels = [ [0,0,0] ] * 512
FCclient.put_pixels(FCpixels)

while True:
    button1 = GPIO.input(19)
    button2 = GPIO.input(16)
    button3 = GPIO.input(26)
    button4 = GPIO.input(20)

    if button1 == True:
        makeLight(naturalLooks[natural_iteration])

        print('Button 1 pressed')
        print('Displaying natural look %s' % str(natural_iteration))

        natural_iteration += 1
        if natural_iteration > len(naturalLooks) - 1:
            natural_iteration = 0

    if button2 == True:
        makeLight(saturatedLooks[saturated_iteration])

        print('Button 2 pressed')
        print('Displaying saturated look %s' % str(saturated_iteration))

        saturated_iteration += 1
        if saturated_iteration > len(saturatedLooks) - 1:
            saturated_iteration = 0

    if button3 == True:
        off()
        print('Button 3 pressed')
        print('Turning off lights')

    if button4 == True:
        makeLight(contrastLooks[contrast_iteration])

        print('Button 4 pressed')
        print('Displaying high contrast look %s' % str(contrast_iteration))

        contrast_iteration += 1
        if contrast_iteration > len(contrastLooks) - 1:
            contrast_iteration = 0

    time.sleep(0.2)
