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



def fireflies(density, frequency, speed, colorPrimary, colorSecondary, colorBackground):
    '''Dots randomly appear on the array, and fade out into a different color'''
    #Establish the background layer
    backgroundLayer = []
    for f in rooms['bedroom']:
        if f.system == 'Fadecandy':
            color = colorCorrect(f, colorBackground)
            backgroundLayer.append([f, color, .5])
        if f.system == 'Hue':
            color = convert(colorCorrect(f, colorBackground))
            command = {'hue': color[0], 'sat': color[1], 'bri': color[2], 'on': True, 'transitiontime': 5}
            bridge.set_light(f.id, command)
    sendMultiCommand(backgroundLayer, controller='bedroomFC')
    #Effect loop
    while True:
    #Grab pixels to put fireflies on
        flyLocations = []
        for i in range(0, density + 1):
            flyLocations.append(random.choice(allMap))
        #All flies appear
        for l in flyLocations:
            sendCommand(l, colorPrimary, fadetime=(.5 * speed), controller='bedroomFC')
            time.sleep(.1 * speed)
        #All flies fade down
        time.sleep(1.3)
        flyCommands = []
        for l in flyLocations:
            flyCommands.append([l, colorSecondary, 4 * speed])
        sendMultiCommand(flyCommands, controller='bedroomFC')
        random.shuffle(flyLocations)
        time.sleep(5 * speed)
        #All Flies go out
        for l in flyLocations:
            sendCommand(l, colorBackground, fadetime=.5, controller='bedroomFC')
            time.sleep(.1 * speed)
        time.sleep(frequency)

fireflies(9, 7, 1, [85,117,0], [17,42,0], [0,12,22])

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
