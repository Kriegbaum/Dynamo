from DYNApatcher import *
import time
from phue import Bridge
from PIL import Image
from PIL import ImageFile
import colorsys
import math
import numpy as np
import random
import shutil
import socket
import json

################################################################################
#                       Control Objects
#This helps with images that were created stupid
ImageFile.LOAD_TRUNCATED_IMAGES = True

#Oour local IP address, tells server where to send data back to
ipSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ipSock.connect(('8.8.8.8', 80))
localIP = ipSock.getsockname()[0]
ipSock.close()

#Hue system control object
print('Initializing hue bridge')
bridge = Bridge(hueIP)

#This will let us see what musicbee is doing
if hasMusicbee:
    print('Initializing Musicbee support')
    from musicbeeipc import *
    from mutagen import File
    mbIPC = MusicBeeIPC()

global_sat = 1
global_bri = 1
global_speed = 1

################################################################################
#                       Network socket operations

def transmit(command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (fadecandyIP, 8000)
    sock.connect(server_address)
    message = json.dumps(command)
    try:
        sock.sendall(message.encode())
    except:
        print('Sending ' + command['type'] + ' failed')
    finally:
        sock.close()

def recieve():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (localIP, 8000)
    sock.bind(server_address)
    print('Listening at', server_address)
    sock.listen(1)
    connection, client_address = sock.accept()
    print('Recieving data from', client_address)
    message = ''
    while True:
        data = connection.recv(16).decode()
        message += data
        if data:
            pass
        else:
            return message
            sock.close()

################################################################################
#                       Fadecandy Initialization
if hasFadecandy:
    print('Initializing Fadecandy Objects')

    def requestArbitration():
        transmit({'type': 'requestArbitration', 'ip': localIP})
        arbitration = recieve()
        arbitration = json.loads(arbitration)
        return arbitration


    def sendCommand(indexrange, rgb, fadetime=5, type='absoluteFade'):
        command = {'type':'absoluteFade', 'color':rgb, 'fade time': fadetime, 'index range': indexrange}
        transmit(command)

    def rippleFade(indexrange, rgb, fadetime=5, type='wipe'):
        sleepTime = fadetime / (indexrange[1] - indexrange[0])
        #0.06s currently represents the minimum time between commands that opcBridge can handle on an RPI3
        #if sleepTime < .06:
        #    sleepTime = .06
        for index in range(indexrange[0], indexrange[1]):
            sendCommand([index, index + 1], rgb, .9)
            time.sleep(sleepTime)

    def dappleFade(indexrange, rgb, fadetime=5):
        indexes = list(range(indexrange[0], indexrange[1]))
        sleepTime = fadetime / (indexrange[1] - indexrange[0])
        #0.06s currently represents the minimum time between commands that opcBridge can handle on an RPI3
        if sleepTime < .06:
            sleepTime = .06
        while indexes:
            index = indexes.pop(random.randrange(0, len(indexes)))
            fadeTime = 1.5 * random.randrange(8, 15) * .1
            sendCommand([index, index + 1], rgb, fadeTime)
            time.sleep(sleepTime)


################################################################################
#                       Functions
def sample_image(image):                                                        #Function for grabbing most common colors in an image, currently unused
    '''this is not used at the moment'''
    im = Image.open(image)
    colors = im.getcolors(100000)                                               #Grabs a list of colors used in images along with count of uses
    color_count = [x[0] for x in colors]                                        #Seperates magnitude values from RGB values
    color_values = [x[1] for x in colors]                                       #Ditto
    min_color_values = []
    min_color_count = []
    for i in range(len(colors)):                                                #This will remove black or near black pixels, no use for a lighting system
        total = sum(color_values[i])                                            #Adds RGB together
        if total > 25:                                                          #Anything below 25 is pretty dark
            min_color_values.append(color_values[i])                            #Constructs new lists minus dark pixels
            min_color_count.append(color_count[i])                              #Removing these pixels from existing lists proved oddly difficult
    top_color = []
    for i in range(25):                                                         #Pulls the top 25 most used colors out of list
        tmp = max(min_color_count)
        tmp_index = min_color_count.index(tmp)                                  #Finds index in count list, grabs same item from value list
        top_color.append(min_color_values[tmp_index])
        del min_color_values[tmp_index]                                         #Remove item from both lists so that max() fill find new item
        del min_color_count[tmp_index]
    return top_color

def randomcolor(image, n):                                                      #Part of the dominant color function, delivers random color off list of top colors
    '''also currently unused'''
    top_color = sample_image(image)
    colorlist = []
    for i in range(n):
        num = random.randrange(0, 24)
        color = convert(top_color[num])
        colorlist.append(color)
    return colorlist

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

def rekt(n):                                                                    #Function delivers the two closest divisible integers of input (n)
    '''as in: get rekt skrub'''
    factors = []
    for i in range(1, n + 1):                                                   #Create a list of integer factors of (n)
        if n % i == 0:
            factors.append(i)
    if len(factors) % 2 == 0:                                                   #Grab middle or just on the large side of middle item for list
        larger = factors[int((len(factors) / 2))]
    else:
        larger = factors[int((len(factors) / 2) - .5)]
    return [larger, int(n / larger)]

def sample_sectors(image, room):                                                #Makes a grid based off number of lights used, samples random pixel from each grid area
    im = Image.open(image)                                                      #Uses pillow PIL fork
    size = im.size                                                              #Grab image dimensions
    if size[0] > size[1]:                                                       #Is it portrait or landscape?
        hdiv = max(rekt(len(room)))                                             #Determine number of horizontal and vertical divisions in grid
        vdiv = min(rekt(len(room)))
    else:
        hdiv = min(rekt(len(room)))
        vdiv = max(rekt(len(room)))
    #FIX: The use of an array here is totally unnessecary, can be done with list function and removes numpy from dependencies
    varray = np.full((vdiv + 1, vdiv + 1), 0, int)                              #Creates blank array based on number of divisions
    harray = np.full((hdiv + 1, hdiv + 1), 0, int)
    for col in range(len(harray)):                                              #Fill array with horizontal division dimensions
        for row in range(len(harray)):
            harray[col][row] = (size[0] / hdiv) * row
    for col in range(len(varray)):                                              #Fill other array with vertical divison dimensions
        for row in range(len(varray)):
            varray[col][row] = (size[1] / vdiv) * row
    pixels = []
    px = im.load()                                                              #Load image, this will be the error point if PIL fails, but the error will likely be at the Image.open() command
    if hdiv >= vdiv:                                                            #Function plays out differently if in portrait or landscape
        for row in range(1, hdiv + 1):                                          #Two commands to iterate through array, can simplify by making a list
            for vrow in range(1, vdiv + 1):
                hrand = random.randrange(harray[0][row - 1], harray[0][row])    #X value for random pixel sample, bounded by grid dimensions
                vrand = random.randrange(varray[0][vrow - 1], varray[0][vrow])  #Y value for random pixel
                tmpix = px[hrand, vrand]                                        #Samples pixel
                if type(tmpix) == int:                                          #If the image is greyscale, it will deliver an integer for value, not RGB
                    tmpix = [tmpix, tmpix, tmpix]                               #We convert to RGB for use in convert()
                pixels.append([tmpix[0], tmpix[1], tmpix[2]])                   #Delivers pixels as a list of lists
    #INVESTIGATE: This may not be nessecary based on the way the previous if: is programmed
    else:                                                                       #Same as previous sequence, but with a portrait format grid
        for row in range(1, vdiv + 1):
            for vrow in range(1, hdiv + 1):
                vrand = random.randrange(varray[0][row - 1], varray[0][row])
                hrand = random.randrange(harray[0][vrow - 1], harray[0][vrow])
                tmpix = px[hrand, vrand]
                if type(tmpix) == int:
                    tmpix = [tmpix, tmpix, tmpix]
                pixels.append([tmpix[0], tmpix[1], tmpix[2]])
    return pixels

def lights_from_image(image, room):                                             #Function takes color list and applies to lights with 10s fade
    it = 0
    colorlist = sample_sectors(image, room)
    for l in range(len(room)):
        print('%s: %s' % (room[l].name, colorlist[it]))
        if hasFadecandy:
            if room[l].system == 'Fadecandy':                                       #See if this is a neopixel strip
                if not room[l].grb:
                    templist = [colorlist[it][1], colorlist[it][0], colorlist[it][2]]   #Useful for swapping RGB to GBR
                    colorlist[it] = templist
                colorlist[it] = colorCorrect(room[l], colorlist[it])
                if sum(colorlist[it]) < 15:
                    colorlist[it] = [0,0,0]
                sendCommand(room[l].indexrange, colorlist[it], 7 * 0.1 * random.randrange(6,14))
                it += 1
        if hasHue:
            if room[l].system == 'Hue':
                colorlist[it] = colorCorrect(room[l], colorlist[it])
                colorlist[it] = convert(colorlist[it])                              #Get color values into something hue API can understand
                com_on = True
                com_sat = colorlist[it][1] * global_sat                             #Adjust saturation according to global adjustment value
                if com_sat > 255:
                    com_sat = 255
                if colorlist[it][1] < 10:
                    com_sat = colorlist[it][1]
                com_bri = colorlist[it][2] * global_bri                             #Adjust brightness according to global adjustment value
                if com_bri > 255:
                    com_bri = 255
                if com_bri < 7:
                    com_on = False
                com_trans = int(70 * global_speed * 0.1 * random.randrange(6,14))      #Adjust transition speed according to global adjustment value
                command = {'hue': colorlist[it][0], 'sat': com_sat , 'bri': com_bri , 'transitiontime': com_trans, 'on' : com_on}
                bridge.set_light(room[l].id, command)
                it += 1
        else:
            print('You fucked up and now there is an improperly classed Fixture in your room!')
            print(l.name, l.system)

def dynamic_image(image, room):
    '''This takes an image and samples colors from it'''
    ex = 0
    while 1 == 1:
        print('...')
        print('...')
        print('Iteration', ex)
        lights_from_image(image, room)
        time.sleep(17)
        ex += 1
        if ex % 3 == 0:
            random.shuffle(room)
            print('\n')
            print('Shuffling fixture order')

if hasMusicbee:
    def dynamic_album(room):                                                        #Will sample image every 15 seconds for new random color
        '''This samples colors off the currently playing album cover'''
        ex = 0
        Album = 'dicks'
        while 1 == 1:
            print('...')
            print('...')
            print('Iteration', ex)
            newAlbum = mbIPC.get_file_tag(MBMD_Album)                               #Pulls trackID of currently playing song

            if newAlbum != Album:                                                   #If there isnt a new song playing, don't do image footwork
                Album = newAlbum
                song = File(mbIPC.get_file_url())
                try:
                    cover = song.tags['APIC:'].data
                    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'artwork.jpg'), 'wb') as img:         #Write temporary file with new album artwork
                        img.write(cover)
                except:
                    print('SHIT SHIT SHIT....')
                    print('APIC tag failed, attempting to read Musicbee Temporary File')
                    shutil.copy(mbIPC.get_artwork_url(), os.path.join(os.path.dirname(os.path.abspath(__file__)), 'artwork.jpg'))
                try:
                    print('Sampling album art for', mbIPC.get_file_tag(MBMD_Album), 'by', mbIPC.get_file_tag(MBMD_Artist))
                except:
                    print('Unable to print name for some reason. Probably because I was too lazy to try and figure out unicode support')
            lights_from_image(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'artwork.jpg'), room)         #Sample colors from temporary file
            time.sleep(18 * global_speed)
            ex += 1
            if ex % 3 == 0:                                                         #Reorder which the grid points that each light samples every once in a while
                random.shuffle(room)
                print('...')
                print('Shuffling fixture order')
def off(room):
    '''Turns off lights in a given room'''
    for l in room:
        if hasFadecandy:
            if l.system == "Fadecandy":
                sendCommand(l.indexrange, [0,0,0])
        if hasHue:
            if l.system == 'Hue':
                bridge.set_light(l.id, 'on', False)
