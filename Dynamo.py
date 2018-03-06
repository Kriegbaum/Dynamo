import opc
import time
import os
from phue import Bridge
from PIL import Image
from PIL import ImageFile
import colorsys
import math
import numpy as np
import random
import shutil
from mutagen import File
from musicbeeipc import *

class Fixture:
    def __init__(self, system, name):
        self.system = system
        self.name = name
        self.indexrange = range(0,0)
        self.colorCorrection = [1, 1, 1]
        self.id = 0
        self.grb = True

#############################################################################
#                           FIXTURE DEFINITIONS
#Fadecandy Fixtures
s1 = Fixture('Fadecandy', 'Windows')
s1.indexrange = range(0,128)
s1.colorCorrection = [1,.8627,.6705]

s3 = Fixture('Fadecandy', 'Fan')
s3.indexrange = range(448,494)
#s3.colorCorrection = [.93725, .79607, 1]
s3.colorCorrection = [1, .8627, 0.6705]

s4 = Fixture('Fadecandy', 'Worklight')
s4.indexrange = range(384,385)
s4.colorCorrection = [1, .97777, 0.63137]

#Hue Fixtures
h1 = Fixture('Hue', 'Coffee Station')
h1.id = 1

h2 = Fixture('Hue', 'Desk Lamp')
h2.id = 2

h3 = Fixture('Hue', 'Entry 2')
h3.id = 3

h4 = Fixture('Hue', 'Reaper')
h4.id = 4

h5 = Fixture('Hue', 'Table Lamp')
h5.id = 5

h6 = Fixture('Hue', 'Flag Left')
h6.id = 6

h7 = Fixture('Hue', 'Flag Right')
h7.id = 7

h8 = Fixture('Hue', 'TV')
h8.id = 8

h10 = Fixture('Hue', 'Dresser')
h10.id = 10

h11 = Fixture('Hue', 'Skull')
h11.id = 11
h11.colorCorrection= [.92,.95,1]

h12 = Fixture('Hue', 'Bedroom Hall')
h12.id = 12

h13 = Fixture('Hue', 'Sink')
h13.id = 13

h14 = Fixture('Hue', 'Pantry')
h14.id = 14

h15 = Fixture('Hue', 'Cabinet Top')
h15.id = 15

h17 = Fixture('Hue', 'Floor Lamp')
h17.id = 17

h18 = Fixture('Hue', 'Drafting Table')
h18.id = 18

h19 = Fixture('Hue', 'Kitchen Door Right')
h19.id = 19

h20 = Fixture('Hue', 'Kitchen Door Left')
h20.id = 20

h21 = Fixture('Hue', 'Morty')
h21.id = 21

h24 = Fixture('Hue', 'Studio Monitors')
h24.id = 24

bedroom = [h2,h10,h11,h17,h18,s1,s3,s4]
living_room = [h3,h5,h6,h7,h8,h19,h20,h4]
kitchen = [h1,h13,h14,h15]
apartment = [h10,h11,h17,h18,s1,s3,s4,h2,h3,h5,h6,h7,h8,h19,h20,h1,h4,h13,h14,h15]
hangout = [h10,h11,h17,h18,s1,s3,s4,h2,h3,h5,h6,h7,h8,h19,h20,h4]

room_dict = {'bedroom': bedroom, 'living room': living_room, 'kitchen': kitchen, 'apartment':apartment, 'hangout':hangout}

################################################################################
#                       Control Objects
#This helps with images that were created stupid
ImageFile.LOAD_TRUNCATED_IMAGES = True


#Hue system control object
bridge = Bridge('192.168.1.31')

#OPC go-between that talks to FCserver
FCclient = opc.Client('192.168.1.145:7890')

#FC control object. 512 RGB pixels, split into eight 64 pixel groups
FCpixels = [ [0,0,0] ] * 512

#This will let us see what musicbee is doing
mbIPC = MusicBeeIPC()

global_sat = 1
global_bri = 1
global_speed = 1

################################################################################
#                       Lighting Initialization
for i in range(193, 256):
    FCpixels[i] = [245,245,190]

FCclient.put_pixels(FCpixels)

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
        if room[l].system == 'Fadecandy':                                       #See if this is a neopixel strip
            if not room[l].grb:
                templist = [colorlist[it][1], colorlist[it][0], colorlist[it][2]]   #Useful for swapping RGB to GBR
                colorlist[it] = templist
            colorlist[it][0] *= room[l].colorCorrection[0]
            colorlist[it][1] *= room[l].colorCorrection[1]
            colorlist[it][2] *= room[l].colorCorrection[2]
            if sum(colorlist[it]) < 15:
                colorlist[it] = [0,0,0]
            for p in room[l].indexrange:
                FCpixels[p] = colorlist[it]
            it += 1

        elif room[l].system == 'Hue':
            colorlist[it][0] *= room[l].colorCorrection[0]
            colorlist[it][1] *= room[l].colorCorrection[1]
            colorlist[it][2] *= room[l].colorCorrection[2]
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
            com_trans = 70 * global_speed                                       #Adjust transition speed according to global adjustment value
            command = {'hue': colorlist[it][0], 'sat': com_sat , 'bri': com_bri , 'transitiontime': com_trans, 'on' : com_on}
            bridge.set_light(room[l].id, command)
            it += 1
        else:
            print('You fucked up and now there is an improperly classed Fixture in your room!')
            print('SHAME ON YOU')
            print('SHAME ON YOU')
            print('SHAME ON YOU')
            print('FUCK YORSELF WHITE BOI')
    FCclient.put_pixels(FCpixels)

def dynamic_image(image, room):
    '''This takes an image and samples colors from it'''
    ex = 0
    while 1 == 1:
        lights_from_image(image, room)
        time.sleep(17)
        ex += 1
        if ex % 3 == 0:
            random.shuffle(room)
            print('Shuffle on iteration', ex)

def dynamic_album(room):                                                        #Will sample image every 15 seconds for new random color
    '''This samples colors off the currently playing album cover'''
    ex = 0
    Album = 'dicks'
    while 1 == 1:
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
                print('Unable to print name for some reason. Probably because I am dumbguy')
        lights_from_image(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'artwork.jpg'), room)         #Sample colors from temporary file
        time.sleep(18 * global_speed)
        ex += 1
        if ex % 3 == 0:                                                         #Reorder which the grid points that each light samples every once in a while
            random.shuffle(room)
            print('Shuffled on iteration', ex)
def off(room):
    '''Turns off lights in a given room'''
    FCpixels = [[0,0,0]] * 512
    for l in room:
        if l.system == "Fadcandy":
            for i in FCpixels:
                i = [0, 0, 0]
        if l.system == 'Hue':
            bridge.set_light(l.id, 'on', False)
    FCclient.put_pixels(FCpixels)

################################################################################
#                       BEGIN MENU

def imageLoop():
    print('Input image name')
    print()
    filedir = os.path.join('E:\\', 'Spidergod', 'Images', 'Color Pallettes')
    pallettes = os.listdir(filedir)
    for f in pallettes:
        print(f)
    filepath = input()
    filepath = os.path.join(filedir, filepath)
    print('Which room?')
    group = room_dict[input().lower()]

    for i in range(len(group)):
        if group[i].system == 'Hue':
            bridge.set_light(group[i].id, 'on', True)

    dynamic_image(filepath, group)

def albumLoop():
    print('Which room?')
    group = room_dict[input().lower()]
    dynamic_album(group)

print('What will it be today?')
subroutine = input().lower()

if subroutine == 'image':
    imageLoop()

if subroutine == 'album':
    albumLoop()

if subroutine == 'off':
    print('Which room?')
    group = room_dict[input().lower()]
    off(group)

else:
    print('Yeah right!')