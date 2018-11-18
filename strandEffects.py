import opc
import time
import math
import numpy as np
import PIL
from DYNAcore import *
import yaml
import random

encoderVal = 0
locationMap = []
intersections = []
allMap = list(range(128,178)) + list(range(192,242)) + list(range(256,306)) + list(range(320,370)) + list(range(384,448))

#SUPPORT FUNCTIONS
def getNextPixel(currentPixel):
    '''Returns the next pixel in the line, or has a chance of returning an
    intersecting pixel if available. If end of the line is reached, function
    will return False and should be handled by encapsulating call'''
    for array in intersections:
        if currentPixel in array:
            nextPixel = random.choice([i for i in array if i != currentPixel])
            return nextPixel
    if currentPixel % 63 == 0:
        return False
    else:
        return currentPixel + 1

def gradientBuilder(stepList):
    '''Typical input:
    [[startValue, steps], [nextValue, steps], [nextValue, steps], [endValue, 1]]
    Values are RGB
    End value should be followed by a one,
    everything else must have at least 1 step'''

    gradientOut = []
    for s in range(len(stepList - 1)):
        gradientOut.append(s[0])

    return gradientOut

def randomPercent(lower, upper):
    '''Returns a decimal percent given integer percentages'''
    return .01 * random.randrange(lower, upper)

def randomPixels(number):
    '''Returns a list [number] items long of random pixels picked from allMap'''
    pixelList = []
    for i in range(0, number + 1):
        pixelList.append(random.choice(allMap))
    return pixelList



#EFFECT LOOP
#ALL OF THESE SHOULD EVENTUALLY HAVE DEFAULT VALUES
def tracers(size, speed, tracerCount, colorPrimary, colorSecondary):
    '''Lines wander around the lighting array'''
    encoderVal = 0
    leadingEdge = 0
    trailingEdge = False
    capturedPixels = [0]
    while True:
        leadingEdge = getNextPixel(leadingEdge)
        capturedPixels.insert(0, leadingEdge)
        if len(capturedPixels) > size:
            trailingEdge = capturedPixels.pop(-1)

def imageSample(density, frequency, speed, stagger, imagedir, imagefile):
    #Render array with beautiful colors
    fullImagePath = os.path.join(imagedir, imagefile)
    colorList = sample_sectors(fullImagePath, allMap)
    megaCommand = []
    iterate = 0
    for p in allMap:
        color = grbFix(colorList[iterate])
        megaCommand.append([p, color, .5 * speed])
        iterate += 1
    sendMultiCommand(megaCommand, controller='bedroomFC')

    while True:
        #Grab some number of pixels
        sampledPix = randomPixels(density)
        colorList = sample_sectors(fullImagePath, sampledPix)
        iterate = 0
        for pix in sampledPix:
            color = grbFix(colorList[iterate])
            sendCommand(pix, color, fadetime=(.5 * speed), controller='bedroomFC')
            if stagger:
                time.sleep(.2 / speed)
            iterate += 1
        if frequency:
            time.sleep(frequency)

imageSample(40,0,1,1,'E:\\Spidergod\\Images\\Color pallettes','goldfish.png')



def fireflies(density=25, frequency=6, speed=1, colorPrimary=[85,117,0], colorSecondary=[8,21,0], colorBackground=[0,12,22]):
    '''Dots randomly appear on the array, and fade out into a different color'''
    #Establish the background layer
    backgroundLayer = []
    for f in rooms['bedroom']:
        if f.system == 'Fadecandy':
            color = colorCorrect(f, colorBackground)
            backgroundLayer.append([f, color, .5])
        if f.system == 'Hue':
            color = convert(colorCorrect(f, colorBackground))
            command = {'hue': color[0], 'sat': color[1], 'bri': color[2], 'on': False, 'transitiontime': 5}
            bridge.set_light(f.id, command)
    sendMultiCommand(backgroundLayer, controller='bedroomFC')
    #Effect loop
    while True:
        #Grab pixels to put fireflies on
        flyLocations = randomPixels(density)
        #All flies appear
        for l in flyLocations:
            sendCommand(l, colorPrimary, fadetime=(.5 * speed), controller='bedroomFC')
            time.sleep(.1 / speed)
        #All flies fade down
        time.sleep(1.3)
        flyCommands = []
        for l in flyLocations:
            flyCommands.append([l, colorSecondary, 3.7 * speed])
        sendMultiCommand(flyCommands, controller='bedroomFC')
        random.shuffle(flyLocations)
        time.sleep(5.0 / speed)
        #All Flies go out
        for l in flyLocations:
            sendCommand(l, colorBackground, fadetime=.5, controller='bedroomFC')
            time.sleep(.1 / speed)
        time.sleep(frequency)


def pallette(imagePath, fadeTime, waitTime, density):
    '''Samples a set of colors off an image, and applies them to random pixels'''

def static(staticMap, fadeTime, globalBrightness):
    '''User definied fixed look for the room'''

def sunrise(realTime, cycleTime, startTime):
    '''Simulates circadian cycle in the room'''

def hyperspace(speed, colorPrimary, colorSecondary):
    '''Radial streaks of color move through the space'''

def shimmer(speed, density, colorSpread, colorPrimary, colorSecondary):
    '''Base color field with flashes of secondary color'''
