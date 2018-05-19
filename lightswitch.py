from DYNAcore import *
import RPi.GPIO as GPIO
import datetime

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
room = rooms['bedroom']
#Function Objects
saturated_iteration = 0
natural_iteration = 0
contrast_iteration = 0

#Spidergod aint no fuckboi
#Spidergod aint never been a fuckboi

#Natural looks

Copper = {
            'Worklight'     : [114,108,113],
            'Fan'           : [120,68,15],
            'Windows'       : [128,134,152],
            'Floor Lamp'    : [44,26,21],
            'Duct'          : [122,106,106],
            'Skull'         : [170,117,56],
            'Corner'        : [144,110,85],
	        'Desk Lamp'     : [120,87,27]
            }

Burma = {
            'Windows'       : [134,89,32],
            'Skull'         : [209,193,169],
            'Worklight'     : [161,116,51],
            'Fan'           : [199,164,96],
            'Corner'        : [177,137,75],
            'Floor Lamp'    : [118,73,16],
            'Duct'          : [168,127,65],
            'Desk Lamp'     : [200,200,25]
            }

Snowy = {
            'Fan'           : [152,150,151],
            'Windows'       : [219,214,220],
            'Duct'          : [120,114,116],
            'Worklight'     : [114,112,115],
            'Floor Lamp'    : [84,87,94],
            'Skull'         : [172,173,188],
            'Corner'        : [106,90,93],
    	    'Desk Lamp'     : [120,120,125]
            }

Japanese = {
            'Windows'       : [123,141,109],
            'Worklight'     : [198,152,68],
            'Corner'        : [195,145,82],
            'Floor Lamp'    : [216,208,189],
            'Duct'          : [224,174,175],
            'Fan'           : [196,171,119],
            'Skull'         : [205,221,200],
	        'Desk Lamp'     : [95,150,160]
            }

Sacred = {
            'Windows'       : [47,183,220],
            'Corner'        : [100,49,25],
            'Duct'          : [81,46,14],
            'Fan'           : [79,60,25],
            'Floor Lamp'    : [85,49,15],
            'Worklight'     : [97,50,12],
            'Skull'         : [44,42,69],
            'Desk Lamp'     : [120,120,115]
            }

Eternity = {
            'Skull'         : [224,182,165],
            'Worklight'     : [225,205,162],
            'Corner'        : [178,110,107],
            'Windows'       : [223,120,101],
            'Fan'           : [174,112,101],
            'Floor Lamp'    : [144,94,97],
            'Duct'          : [128,85,92],
            'Desk Lamp'     : [170,95,85]
            }

Warm = {
            'Skull'         : [255,197,143],
            'Worklight'     : [255,197,143],
            'Corner'        : [255,197,143],
            'Windows'       : [255,197,143],
            'Fan'           : [255,197,143],
            'Floor Lamp'    : [255,197,143],
            'Duct'          : [255,197,143],
            'Desk Lamp'     : [255,197,143]
            }

#Saturated looks

Jelly = {
            'Floor Lamp'    : [0,35,111],
            'Duct'          : [239,30,0],
            'Corner'        : [1,98,175],
            'Windows'       : [254,138,1],
            'Fan'           : [0,0,255],
            'Skull'         : [95,45,0],
            'Worklight'     : [0,174,198],
            'Desk Lamp'     : [112,112,128]
            }


Valtari = {
            'Skull'         : [103,122,4],
            'Floor Lamp'    : [6,71,12],
            'Corner'        : [110,117,14],
            'Windows'       : [101,55,0],
            'Fan'           : [6,71,12],
            'Worklight'     : [110,117,14],
            'Duct'          : [230,115,6],
            'Desk Lamp'     : [95,130,70]
            }

Vaporwave = {
            'Worklight'     : [120,200,164],
            'Windows'       : [188,110,241],
            'Skull'         : [117,35,150],
            'Fan'           : [96,71,126],
            'Corner'        : [70,200,135],
            'Duct'          : [129,31,142],
            'Floor Lamp'    : [120,168,146],
            'Desk Lamp'     : [0,110,170]
            }

Intersection = {
            'Skull'         : [219,118,175],
            'Floor Lamp'    : [135,88,202],
            'Corner'        : [207,112,204],
            'Windows'       : [208,89,153],
            'Fan'           : [75,40,190],
            'Duct'          : [80,47,150],
            'Worklight'     : [79,39,73],
            'Desk Lamp'     : [190,90,150]
            }

Eiffel = {
            'Fan'           : [255,197,63],
            'Skull'         : [99,52,11],
            'Worklight'     : [128,72,0],
            'Corner'        : [123,50,0],
            'Windows'       : [119,62,7],
            'Duct'          : [112,64,0],
            'Floor Lamp'    : [87,43,8],
	        'Desk Lamp'     : [255,170,10]
            }

Umbrella = {
            'Worklight'     : [43,133,162],
            'Skull'         : [24,100,144],
            'Fan'           : [255,255,255],
            'Corner'        : [26,120,144],
            'Floor Lamp'    : [165,64,107],
            'Duct'          : [7,75,138],
            'Windows'       : [165,64,107],
            'Desk Lamp'     : [50,50,128]
            }

Toplight = {
            'Worklight'     : [0,0,0],
            'Skull'         : [0,0,0],
            'Fan'           : [70,150,220],
            'Corner'        : [0,0,0],
            'Floor Lamp'    : [0,0,0],
            'Duct'          : [0,0,0],
            'Windows'       : [0,0,0],
            'Desk Lamp'     : [0,0,0]
            }

Blinds = {
            'Worklight'     : [0,0,0],
            'Skull'         : [0,0,0],
            'Fan'           : [0,0,0],
            'Corner'        : [0,0,0],
            'Floor Lamp'    : [0,0,0],
            'Duct'          : [0,0,0],
            'Windows'       : [255,197,110],
            'Desk Lamp'     : [40,40,20]
            }

Cabinet = {
            'Worklight'      : [0,0,0],
	        'Skull'	         : [0,0,0],
	        'Fan'            : [0,0,0],
	        'Corner'         : [90,40,25],
	        'Floor Lamp'     : [0,0,0],
	        'Duct'           : [0,0,0],
	        'Windows'        : [0,0,0],
            'Desk Lamp'      : [0,0,0]
	   }

Void = {
            'Worklight'      : [183,176,218],
	        'Skull'	         : [200,72,159],
	        'Fan'            : [74,11,203],
	        'Corner'         : [28,0,28],
	        'Floor Lamp'     : [39,2,20],
	        'Duct'           : [144,0,171],
	        'Windows'        : [218,211,218],
            'Desk Lamp'      : [5,0,6]
	   }

naturalLooks = [Copper, Burma, Snowy, Japanese, Sacred, Eternity, Warm]
saturatedLooks = [Jelly, Vaporwave, Intersection, Eiffel, Valtari, Umbrella, Void]
contrastLooks = [Toplight, Blinds, Cabinet]


def makeLight(look):
    for l in room:
        if l.system == 'Fadecandy':
            color = colorCorrect(l, look[l.name])
            sendCommand(l.indexrange, color, .5)
            time.sleep(0.05)

        elif l.system == 'Hue':
            if look[l.name] == [0,0,0]:
                command = {'on' : False}
            else:
                color = convert(colorCorrect(l, look[l.name]))
                command = {'hue': color[0], 'sat': color[1], 'bri': color[2], 'on': True, 'transitiontime': 5}
            bridge.set_light(l.id, command)
            time.sleep(0.05)

        else:
            print('You fucked up and now there is an improperly classed Fixture in your room!')
            print(l.name)
            print(l.system)

def off():
    for l in room:
        if l.system == 'Hue':
            bridge.set_light(l.id, 'on', False)
        if l.system == 'Fadecandy':
            sendCommand(l.indexrange, [0,0,0], 0.5)
        bridge.set_light(24, 'on', False)



sendCommand([0,128], [255,255,255], 1)
time.sleep(1)
sendCommand([0,128], [0,0,0], 1)
time.sleep(1)
sendCommand([0,128], [255,255,255], 2)
time.sleep(1)
sendCommand([0,128], [0,0,0], 2)

button1last = False
button2last = False
button3last = False
button4last = False

while True:
    button1 = GPIO.input(19)
    button2 = GPIO.input(16)
    button3 = GPIO.input(26)
    button4 = GPIO.input(20)


    if button1 and not button1last:
        sendCommand([320,340], [220,228,245])
        makeLight(naturalLooks[natural_iteration])
        print(datetime.datetime.now())
        print('Button 1 pressed')
        print('Displaying natural look %s' % str(natural_iteration))

        natural_iteration += 1
        if natural_iteration > len(naturalLooks) - 1:
            natural_iteration = 0
        button1last = True

    elif button2 and not button2last:
        sendCommand([320,340], [220,228,245])
        makeLight(saturatedLooks[saturated_iteration])
        print(datetime.datetime.now())
        print('Button 2 pressed')
        print('Displaying saturated look %s' % str(saturated_iteration))

        saturated_iteration += 1
        if saturated_iteration > len(saturatedLooks) - 1:
            saturated_iteration = 0
        button2last = True

    elif button3 and not button3last:
        off()
        sendCommand([320,340], [0,0,0])
        print(datetime.datetime.now())
        print('Button 3 pressed')
        print('Turning off lights')
        button3last = True

    elif button4 and not button4last:
        sendCommand([320,340], [245,50,0])
        makeLight(contrastLooks[contrast_iteration])
        print(datetime.datetime.now())
        print('Button 4 pressed')
        print('Displaying high contrast look %s' % str(contrast_iteration))

        contrast_iteration += 1
        if contrast_iteration > len(contrastLooks) - 1:
            contrast_iteration = 0
        button4last = True

    else:
        button1last = False
        button2last = False
        button3last = False
        button4last = False

    time.sleep(0.7)
