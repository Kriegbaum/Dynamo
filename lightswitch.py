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
#Spidergod aint never even SEEn a fuckboi

#Natural looks

Copper = {
            'Worklight'     : [114,108,113],
            'Fan'           : [120,68,15],
            'Office Closet' : [128,134,152],
            'Iris'          : [44,26,21],
            'Print'         : [122,106,106],
            'Whiteboard'    : [170,117,56],
            'Workbench'     : [144,110,85],
	        'Desk Lamp'     : [120,87,27]
            }

Burma = {
            'Office Closet' : [134,89,32],
            'Whiteboard'    : [209,193,169],
            'Worklight'     : [161,116,51],
            'Fan'           : [199,164,96],
            'Workbench'     : [177,137,75],
            'Iris'          : [118,73,16],
            'Print'         : [168,127,65],
            'Desk Lamp'     : [200,200,25]
            }

Snowy = {
            'Fan'           : [152,150,151],
            'Office Closet' : [219,214,220],
            'Print'         : [120,114,116],
            'Worklight'     : [114,112,115],
            'Iris'          : [84,87,94],
            'Whiteboard'    : [172,173,188],
            'Workbench'     : [106,90,93],
    	    'Desk Lamp'     : [120,120,125]
            }

Japanese = {
            'Office Closet' : [123,141,109],
            'Worklight'     : [198,152,68],
            'Workbench'     : [195,145,82],
            'Iris'          : [216,208,189],
            'Print'         : [224,174,175],
            'Fan'           : [196,171,119],
            'Whiteboard'    : [205,221,200],
	        'Desk Lamp'     : [95,150,160]
            }

Sacred = {
            'Office Closet' : [47,183,220],
            'Workbench'     : [100,49,25],
            'Print'         : [81,46,14],
            'Fan'           : [79,60,25],
            'Iris'          : [85,49,15],
            'Worklight'     : [97,50,12],
            'Whiteboard'    : [44,42,69],
            'Desk Lamp'     : [120,120,115]
            }

Eternity = {
            'Whiteboard'    : [224,182,165],
            'Worklight'     : [225,205,162],
            'Workbench'     : [178,110,107],
            'Office Closet' : [223,120,101],
            'Fan'           : [174,112,101],
            'Iris'          : [144,94,97],
            'Print'         : [128,85,92],
            'Desk Lamp'     : [170,95,85]
            }

Warm = {
            'Whiteboard'    : [255,197,143],
            'Worklight'     : [255,197,143],
            'Workbench'     : [255,197,143],
            'Office Closet' : [255,197,143],
            'Fan'           : [255,197,143],
            'Iris'          : [255,197,143],
            'Print'         : [255,197,143],
            'Desk Lamp'     : [255,197,143]
            }

#Saturated looks

Jelly = {
            'Iris'          : [0,35,111],
            'Print'         : [239,30,0],
            'Workbench'     : [1,98,175],
            'Office Closet' : [254,138,1],
            'Fan'           : [0,0,255],
            'Whiteboard'    : [95,45,0],
            'Worklight'     : [0,174,198],
            'Desk Lamp'     : [112,112,128]
            }


Valtari = {
            'Whiteboard'    : [103,122,4],
            'Iris'          : [16,61,12],
            'Workbench'     : [110,117,14],
            'Office Closet' : [101,55,0],
            'Fan'           : [6,71,12],
            'Worklight'     : [110,117,14],
            'Print'         : [230,115,6],
            'Desk Lamp'     : [95,130,70]
            }

Vaporwave = {
            'Worklight'     : [120,200,164],
            'Office Closet' : [188,110,241],
            'Whiteboard'    : [117,35,150],
            'Fan'           : [96,71,126],
            'Workbench'     : [70,200,135],
            'Print'         : [129,31,142],
            'Iris'          : [120,168,146],
            'Desk Lamp'     : [0,110,170]
            }

Intersection = {
            'Whiteboard'    : [219,118,175],
            'Iris'          : [135,88,202],
            'Workbench'     : [207,112,204],
            'Office Closet' : [208,89,153],
            'Fan'           : [75,40,190],
            'Print'         : [80,47,150],
            'Worklight'     : [79,39,73],
            'Desk Lamp'     : [190,90,150]
            }

Eiffel = {
            'Fan'           : [255,197,63],
            'Whiteboard'    : [99,52,11],
            'Worklight'     : [128,72,0],
            'Workbench'     : [123,50,0],
            'Office Closet' : [119,62,7],
            'Print'         : [112,64,0],
            'Iris'          : [87,43,8],
	        'Desk Lamp'     : [255,170,10]
            }

Umbrella = {
            'Worklight'     : [43,133,162],
            'Whiteboard'    : [24,100,144],
            'Fan'           : [255,255,255],
            'Workbench'     : [26,120,144],
            'Iris'          : [165,64,107],
            'Print'         : [7,75,138],
            'Office Closet' : [165,64,107],
            'Desk Lamp'     : [50,50,128]
            }

Toplight = {
            'Worklight'     : [0,0,0],
            'Whiteboard'    : [0,0,0],
            'Fan'           : [70,150,220],
            'Workbench'     : [0,0,0],
            'Iris'          : [0,0,0],
            'Print'         : [0,0,0],
            'Office Closet' : [0,0,0],
            'Desk Lamp'     : [0,0,0]
            }

Blinds = {
            'Worklight'     : [0,0,0],
            'Whiteboard'    : [0,0,0],
            'Fan'           : [0,0,0],
            'Workbench'     : [0,0,0],
            'Iris'          : [0,0,0],
            'Print'         : [0,0,0],
            'Office Closet' : [255,197,110],
            'Desk Lamp'     : [40,40,20]
            }

Cabinet = {
            'Worklight'      : [0,0,0],
	        'Whiteboard'	 : [0,0,0],
	        'Fan'            : [0,0,0],
	        'Workbench'      : [90,40,25],
	        'Iris'           : [0,0,0],
	        'Print'          : [0,0,0],
	        'Office Closet'  : [0,0,0],
            'Desk Lamp'      : [0,0,0]
	   }

Void = {
            'Worklight'      : [183,176,218],
	        'Whiteboard'	 : [200,72,159],
	        'Fan'            : [74,11,203],
	        'Workbench'      : [28,0,28],
	        'Iris'           : [39,2,20],
	        'Print'          : [144,0,171],
	        'Office Closet'  : [218,211,218],
            'Desk Lamp'      : [5,0,6]
	   }

naturalLooks = [Copper, Burma, Snowy, Japanese, Sacred, Eternity, Warm]
saturatedLooks = [Jelly, Vaporwave, Intersection, Eiffel, Valtari, Umbrella, Void]
contrastLooks = [Toplight, Blinds, Cabinet]


def makeLight(look):
    setArbitration(False)
    for l in room:
        if l.system == 'Fadecandy':
            color = colorCorrect(l, look[l.name])
            sendCommand(l, color, .5)

        elif l.system == 'Hue':
            if look[l.name] == [0,0,0]:
                command = {'on' : False}
            else:
                color = convert(colorCorrect(l, look[l.name]))
                command = {'hue': color[0], 'sat': color[1], 'bri': color[2], 'on': True, 'transitiontime': 5}
            bridge.set_light(l.id, command)

        else:
            print('You fucked up and now there is an improperly classed Fixture in your room!')
            print(l.name)
            print(l.system)

def off():
    for l in room:
        if l.system == 'Hue':
            bridge.set_light(l.id, 'on', False)
        if l.system == 'Fadecandy':
            sendCommand(l, [0,0,0], 0.5)
        bridge.set_light(24, 'on', False)



sendCommand([0,128], [255,255,255], 1, controller='officeFC')
time.sleep(1)
sendCommand([0,128], [0,0,0], 1, controller='officeFC')
time.sleep(1)
sendCommand([0,128], [255,255,255], 1, controller='officeFC')
time.sleep(1)
sendCommand([0,128], [0,0,0], 2, controller='officeFC')

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
        makeLight(naturalLooks[natural_iteration])
        print(datetime.datetime.now())
        print('Button 1 pressed')
        print('Displaying natural look %s' % str(natural_iteration))

        natural_iteration += 1
        if natural_iteration > len(naturalLooks) - 1:
            natural_iteration = 0
        button1last = True

    elif button2 and not button2last:
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
        print(datetime.datetime.now())
        print('Button 3 pressed')
        print('Turning off lights')
        button3last = True

    elif button4 and not button4last:
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

    time.sleep(0.2)
