from phue import Bridge
import os
import time
from PIL import Image
from PIL import ImageFile
import colorsys
import math
import numpy as np
import random
import plistlib
from mutagen import File
import mutagen.mp4
from Foundation import *
from ScriptingBridge import *


bridge = Bridge('10.0.0.10')                                                    #Hardcoded for my system, fix this later
bedroom = [7,8,10,11,12,14]                                                     #Hardcoded for my system, fix this later
living_room = [1,2,3,4,5,6,13]                                                  #Hardcoded for my system, fix this later

iTunes = SBApplication.applicationWithBundleIdentifier_("com.apple.iTunes")     #Grab iTunes parameters from scripting bridge

tunes_library_path = '/Users/andykauff/Music/iTunes/iTunes Music Library.xml'   #Hardcoded for my system, fix this later
print('loading itunes library...')
tunes_library = plistlib.readPlist(tunes_library_path)                          #Loads iTunes library into a massive dictionary
print('LOADED')

ImageFile.LOAD_TRUNCATED_IMAGES = True                                          #This helps with images that were created stupid


def setup():                                                                    #Obtain hue system info from user
    print('Input bridge IP address')
    bridgeip = input()
    bridge = Bridge(bridgeip)
    settings_body = 'Bridge IP:\n' + bridgeip + '\n'                            #Add bridge ip to settings
    settings = open(settings_path, 'w')                                         #Create or open settings file
    settings.write(settings_body)                                               #Write settings to settings file
    settings.close()
    print('Within the next 30 seconds, press the bridge connect button')        #Bridge button is security feature, grants access to this program
    time.sleep(30)                                                              #Give user time to physically reach bridge
    bridge.connect()                                                            #Connect to bridge


def getsettings():                                                              #Grab settings if they have been made
    script_dir = os.path.dirname(os.path.abspath(__file__))                     #Set directory to script's location
    settings_path = script_dir + '/hue_settings.txt'
    if os.path.exists(settings_path):                                           #Check to see if settings already exist
        settings = open(settings_path, 'r')
        settings.readline()
        bridge = Bridge(readline())
    else:
        setup()                                                                 #If settings do not exist, run user through setup

def get_song_path(trackID):                                                     #Let's grab this song's filepath
    path = tunes_library['Tracks'][str(trackID)]['Location']                    #Nabs filepath from library xml, but the format its stored in is not useable, so:
    path = path.replace('file://', '')                                          #Strip out extraneous info
    path_list = path.split('%')
    newpath = bytes(path_list[0], 'utf-8')                                      #We need this to be a bytes literal, but can't do it befor the split command
    if len(path_list) > 1:                                                      #Skip process if no special characters
        for i in range(1,len(path_list)):                                       #Iterate through split list
            tmpbyte = path_list[i][0:2]                                         #Grab hex value after first split
            newbyte = bytes([int(str(tmpbyte), 16)])                            #Make that hex value into its ascii value and then convert the ascii value back into the same byte, but with proper formatting
            newpath += newbyte + bytes(path_list[i][2:len(path_list[i])], 'utf-8')  #Drop that byte and its associated chunk into the new filepath
    newpath = newpath.decode('utf-8')                                           #Decode remaining special characters
    return newpath

def sample_image(image):                                                        #Function for grabbing most common colors in an image, currently unused
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

def convert(RGB):                                                               #Takes RGB value and delivers the flavor of HSV that the hue api uses
    R = RGB[0] / 255                                                            #colorsys takes values between 0 and 1, PIL delivers between 0 and 255
    G = RGB[1] / 255
    B = RGB[2] / 255
    hsv = colorsys.rgb_to_hsv(R, G, B)                                          #Makes standard HSV
    hsv_p = [int(hsv[0] * 360 * 181.33), int(hsv[1] * 255), int(hsv[2] * 255)]  #Converts to Hue api HSV
    return hsv_p

def randomcolor(image, n):                                                      #Part of the dominant color function, delivers random color off list of top colors
    top_color = sample_image(image)
    colorlist = []
    for i in range(n):
        num = random.randrange(0, 24)
        color = convert(top_color[num])
        colorlist.append(color)
    return colorlist

def rekt(n):                                                                    #Function delivers the two closest divisible integers of input (n)
    factors = []
    for i in range(1, n + 1):                                                   #Create a list of integer factors of (n)
        if n % i == 0:
            factors.append(i)
    if len(factors) % 2 == 0:                                                   #Grab middle or just on the large side of middle item for list
        larger = factors[int((len(factors) / 2))]
    else:
        larger = factors[int((len(factors) / 2) - .5)]
    return [larger, int(n / larger)]                                            #Delivers integers, these will be the dimensions of the grid for sample_sectors

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
    for i in range(len(pixels)):                                                #Sends all pixels to convert() to get HSV
        pixels[i] = convert(pixels[i])
    return pixels

def lights_from_image(image, room):                                             #Function takes color list and applies to lights with 10s fade
    it = 0
    colorlist = sample_sectors(image, room)
    for l in room:
        command = {'hue': colorlist[it][0], 'sat': colorlist[it][1], 'bri': colorlist[it][2], 'transitiontime': 100}
        bridge.set_light(l, command)
        it += 1

def dynamic_image(room):                                                        #Will sample image every 15 seconds for new random color
    ex = 0
    trackID = iTunes.currentTrack().databaseID()
    while 1 == 1:
        newID = iTunes.currentTrack().databaseID()                              #Pulls trackID of currently playing song
        try:
            if tunes_library['Tracks'][str(newID)]['Album'] != tunes_library['Tracks'][str(trackID)]['Album'] or ex == 0:                                                    #If there isnt a new song playing, don't do image footwork
                trackID = newID
                song_path = get_song_path(trackID)
                artwork_dir = os.path.dirname(os.path.abspath(__file__))            #Set directory to where current script is
                artwork_path = artwork_dir + '/artwork.jpg'
                if song_path[len(song_path) - 4:] == '.m4a':                        #adds m4a support
                    song = mutagen.mp4.MP4(song_path)
                    cover = bytes(song['covr'][0])
                    with open(artwork_path, 'wb') as img:                           # Write temporary file with new album artwork
                        img.write(cover)
                else:
                    song = File(song_path)                                          #Pull filepath of song, load it up
                    try:
                        artwork = song.tags['APIC:'].data                           #Load up image data for album artwork on song
                    except:
                        time.sleep(15)
                        continue
                    with open(artwork_path, 'wb') as img:                           #Write temporary file with new album artwork
                        img.write(artwork)
                print('Sampling album art for', tunes_library['Tracks'][str(trackID)]['Album'], 'by', tunes_library['Tracks'][str(trackID)]['Artist'])
            lights_from_image(artwork_path, room)                                   #Sample colors from temporary file
        except:
            print('Nothing playing, setting lights to white')
            command = {'bri': 255, 'sat': 0}
            bridge.set_light(room, command)
        time.sleep(15)
        ex += 1
        if ex % 3 == 0:                                                         #Reorder which the grid points that each light samples every once in a while
            random.shuffle(room)
            print('Shuffled on iteration', ex)

print('Which room?')
group = eval(input())
bridge.set_light(group, 'on', True)                                             #Turn lights on before executing
bridge.set_light(16, 'on', True)

dynamic_image(group)
