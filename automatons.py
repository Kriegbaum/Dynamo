from DYNAcore import *
from datetime import datetime
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
import atexit
################################################################################
#                       Control Objects
#This helps with images that were created stupid
ImageFile.LOAD_TRUNCATED_IMAGES = True

#This will let us see what musicbee is doing
try:
    print('Initializing Musicbee support')
    from musicbeeipc import *
    from mutagen import File
    mbIPC = MusicBeeIPC()
except:
    print('...')
    print('Musicbee support not found, disabling music features')
    hasMusicbee = False

def rekt(n):
    #Function delivers the two closest divisible integers of input (n)
    '''as in: get rekt skrub'''
    factors = []
    #Create a list of integer factors of (n)
    for i in range(1, n + 1):
        if n % i == 0:
            factors.append(i)
    #Grab middle or just on the large side of middle item for list
    if len(factors) % 2 == 0:
        larger = factors[int((len(factors) / 2))]
    else:
        larger = factors[int((len(factors) / 2) - .5)]
    return [larger, int(n / larger)]

def sample_sectors(image, count):
    '''Makes a grid based off number of lights used, samples random pixel from each grid area'''
    #Uses pillow PIL fork
    im = Image.open(image)
    #Grab image dimensions
    size = im.size
    #Is it portrait or landscape?
    if size[0] > size[1]:
    #Determine number of horizontal and vertical divisions in grid
        hdiv = max(rekt(count))
        vdiv = min(rekt(count))
    else:
        hdiv = min(rekt(count))
        vdiv = max(rekt(count))
    #FIX: The use of an array here is totally unnessecary, can be done with list function and removes numpy from dependencies
    #Creates blank array based on number of divisions
    varray = np.full((vdiv + 1, vdiv + 1), 0, int)
    harray = np.full((hdiv + 1, hdiv + 1), 0, int)
    #Fill array with horizontal division dimensions
    for col in range(len(harray)):
        for row in range(len(harray)):
            harray[col][row] = (size[0] / hdiv) * row
    #Fill other array with vertical divison dimensions
    for col in range(len(varray)):
        for row in range(len(varray)):
            varray[col][row] = (size[1] / vdiv) * row
    pixels = []
    #Load image, this will be the error point if PIL fails, but the error will likely be at the Image.open() command
    px = im.load()
    #Function plays out differently if in portrait or landscape
    if hdiv >= vdiv:
        #Two commands to iterate through array, can simplify by making a list
        for row in range(1, hdiv + 1):
            for vrow in range(1, vdiv + 1):
                #X value for random pixel sample, bounded by grid dimensions
                hrand = random.randrange(harray[0][row - 1], harray[0][row])
                #Y value for random pixel
                vrand = random.randrange(varray[0][vrow - 1], varray[0][vrow])
                #Samples pixel
                tmpix = px[hrand, vrand]
                #If the image is greyscale, it will deliver an integer for value, not RGB
                if type(tmpix) == int:
                    #We convert to RGB
                    tmpix = [tmpix, tmpix, tmpix]
                #Delivers pixels as a list of lists
                pixels.append([tmpix[0], tmpix[1], tmpix[2]])
    #INVESTIGATE: This may not be nessecary based on the way the previous if: is programmed
    else:
        #Same as previous sequence, but with a portrait format grid
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
    colorlist = sample_sectors(image, len(room.fixtureList))
    scene = {}
    for f in room.fixtureList:
        print('%s: %s' % (f.name, colorlist[it]))
        scene[f.name] = [colorlist[it], 7 * 0.1 * random.randrange(6,14)]
        it += 1
    room.scene(scene)

def dynamic_image(image, room):
    '''This takes an image and samples colors from it'''
    ex = 0
    room.setArbitration('Dynamic Image')
    while True:
        if room.getArbitration():
            print('...')
            print('...')
            print('Iteration', ex)
            lights_from_image(image, room)
            time.sleep(17)
            ex += 1
            if ex % 3 == 0:
                random.shuffle(room.fixtureList)
                print('\n')
                print('Shuffling fixture order')
        else:
            print('Halting automated routine, overriden by user')
            break

def image_cycle(directory, room):
    cycleIterator = 0
    chosenDir = os.path.join(pallettesDir, directory)
    pallettes = os.listdir(chosenDir)
    directoryIterator = random.randrange(0, len(pallettes))
    room.setArbitration('Dynamic Image Cycle')
    while True:
        if room.getArbitration():
            print('...')
            print('...')
            print('Iteration', cycleIterator)
            print('Sampling ', pallettes[directoryIterator])
            image = os.path.join(chosenDir, pallettes[directoryIterator])
            lights_from_image(image, room)
            time.sleep(17)
            cycleIterator += 1
            if cycleIterator % 3 == 0:
                random.shuffle(room.fixtureList)
                print('\n')
                print('Shuffling fixture order')
            if cycleIterator % 23 == 0:
                directoryIterator += 1
                if directoryIterator > len(pallettes):
                    directoryIterator = 0
        else:
            print('Halting automated routine, overriden by user')
            break


if hasMusicbee:
    def dynamic_album(room):                                                        #Will sample image every 15 seconds for new random color
        '''This samples colors off the currently playing album cover'''
        ex = 0
        Album = 'dicks'
        room.setArbitration('Dynamic Album Cover, Musicbee')
        while True:
            if room.getArbitration()):
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
                        try:
                            shutil.copy(mbIPC.get_artwork_url(), os.path.join(os.path.dirname(os.path.abspath(__file__)), 'artwork.jpg'))
                        except:
                            print('APIC tag and musicbee backup option have both failed. This is likely because the album lacks artwork')
                    try:
                        print('Sampling album art for', mbIPC.get_file_tag(MBMD_Album), 'by', mbIPC.get_file_tag(MBMD_Artist))
                    except:
                        print('Unable to print name for some reason. Probably because I was too lazy to try and figure out unicode support')
                lights_from_image(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'artwork.jpg'), room)         #Sample colors from temporary file
                time.sleep(18)
                ex += 1
                if ex % 3 == 0:                                                         #Reorder which the grid points that each light samples every once in a while
                    random.shuffle(room.fixtureList)
                    print('...')
                    print('Shuffling fixture order')
            else:
                print('Halting automated routine, overriden by user')
                break

def circadianLookup(city):
    '''retuns a color temperature value given an astral city object'''
    '''Data points:
    (-36, 2700)
    (-18, 15000)
    (0, 7000)
    (18, 10000)
    (90, 7000)
    (0, 2000)
    (-18, 10000)
    (-36, 2700)
    '''
    sun = city.sun()
    timezone = sun['sunrise'].tzinfo
    now = datetime.now(tz=timezone)
    elevation = city.solar_elevation()
    print('Sun elevation: ' + str(elevation))
    #Are we after sunset or before sunrise?
    if elevation < 0:
        #In the darkest part of the night, lights go to natural tungsten lamp, but a little warmer
        if elevation <= -36:
            return 2700
        #Just before sunrise, lights get very cool to help wake you up
        if now <= sun['sunrise']:
            if elevation <= -18:
                return ((2050 * elevation) / 3.0) + 27300
            else:
                return 7000 - ((4000 * elevation) / 9.0)
        elif now >= sun['sunset']:
            if elevation <= -18:
                return ((3650 * elevation) / 9.0) + 17300
            else:
                return 2000 - ((4000 * elevation) / 9.0)
        #There should be no cases outside of the above tests
        else:
            print('Sun elevation is negative, but it is after sunrise and before sunset, something is not right here')
            return False
    #The sun will pass each elevation point twice, but the light should continue to get warmer
    #So we must seperate before and after noon
    else:
        if now <= sun['noon']:
            #There is a second spike in color temperature after sunrise
            if elevation < 18:
                return ((500 * elevation) / 3.0) + 7000
            else:
                return 10750 - ((125 * elevation) / 3.0)
        else:
            return ((500 * elevation) / 9.0) + 2000


def circadian(room):
    print('Circadian cycle selected, loading Astral module...')
    from astral import Astral
    print('Astral module loaded!')
    cityName = 'Chicago'
    a = Astral()
    city = a[cityName]
    controllerList = gatherControllers(room)
    while True:
        if gatherArbitration(controllerList):
            kelvin = circadianLookup(city)
            print('Based on sun elevation, setting lights to: %s Kelvin' % kelvin)
            rgb = cctRGB(kelvin)
            print('Kelvin parsed to ' + str(rgb))
            rgbRoom(room, rgb, 40)
            print('...')
            print('')
            time.sleep(120)
        else:
            print('Circadian routine interrupted by manual override')
