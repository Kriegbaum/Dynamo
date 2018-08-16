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



def fireflies(density, frequency, speed, colorPrimary, colorSecondary):
    '''Dots randomly appear on the array, and fade out into a different color'''

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
