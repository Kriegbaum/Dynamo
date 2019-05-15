import time
import math
import numpy as np
import PIL
from Tantallion import *
import yaml
import random
import threading
from automatons import *

#Build 5x50 array, rows and columns
locationMap = [[128], [192], [256], [320], [384]]
for i in range(49):
    for x in locationMap:
        x.append(x[-1] + 1)
#Locations where pixels touch each other
intersections = [[128, 192, 256, 320, 384]]
#Every index in a one dimensional array
allMap = list(range(128,178)) + list(range(192,242)) + list(range(256,306)) + list(range(320,370)) + list(range(384,434))

#Load in our lighting rig
patch = Patch()
controller = patch.controller('bedroomFC')
room = patch.room('bedroom')

def bridgeValues(totalSteps, start, end):
    '''Generator that creates interpolated steps between a start and end value
    Accepts an rgb value, outputs rgb values'''
    newRGB = start
    diffR = (end[0] - start[0]) / float(totalSteps)
    diffG = (end[1] - start[1]) / float(totalSteps)
    diffB = (end[2] - start[2]) / float(totalSteps)
    for i in range(totalSteps - 1):
        newRGB = [newRGB[0] + diffR, newRGB[1] + diffG, newRGB[2] + diffB]
        yield [int(newRGB[0]), int(newRGB[1]), int(newRGB[2])]
    return end

def randomPercent(lower, upper):
    '''Returns a random decimal percent given bounds in integers'''
    return .01 * random.randrange(lower, upper)

def gradientBuilder(stepList):
    '''Typical input:
    [[startValue, THROWAWAY], [nextValue, steps], [nextValue, steps], [endValue, steps]]
    Values are RGB
    Number of steps in first color are discarded
    everything else must have at least 1 step'''
    gradientOut = []
    gradientOut.append(stepList[0][0])
    for s in range(1, len(stepList)):
        start = stepList[s - 1][0]
        steps = stepList[s][1]
        end = stepList[s][0]
        bridgeGenerator = bridgeValues(steps, start, end)
        for c in range(steps - 1):
            gradientOut.append(next(bridgeGenerator))
    return gradientOut

class PixelArray():
    def __init__(self, allMap, locationMap, intersections, room, controller):
        self.locationMap = locationMap
        self.allMap = allMap
        self.intersections = intersections
        self.room = room
        self.controller = controller

    #SUPPORT FUNCTIONS
    def getNextPixel(self, currentPixel):
        '''Returns the next pixel in the line, or has a chance of returning an
        intersecting pixel if available. If end of the line is reached, function
        will return False and should be handled by encapsulating call'''
        for array in self.intersections:
            if currentPixel in array:
                nextPixel = random.choice([i for i in array if i != currentPixel])
                return nextPixel
        if currentPixel % 63 == 0:
            return False
        else:
            return currentPixel + 1

    def randomPixels(self, number):
        '''Returns a list [number] items long of random pixels picked from allMap'''
        pixelList = []
        for i in range(0, number + 1):
            pixelList.append(random.choice(self.allMap))
        return pixelList

    #EFFECT LOOPS
    #ALL OF THESE SHOULD EVENTUALLY HAVE DEFAULT VALUES FOR EVERY PARAMETER
    def tracers(self, colorPrimary, colorSecondary, size=3, speed=1, tracerCount=2):
        '''Lines wander around the lighting array
        NOT FINISHED'''
        leadingEdge = 0
        trailingEdge = False
        capturedPixels = [0]
        while True:
            leadingEdge = self.getNextPixel(leadingEdge)
            capturedPixels.insert(0, leadingEdge)
            if len(capturedPixels) > size:
                trailingEdge = capturedPixels.pop(-1)

    def imageSample(self, imagedir, imagefile, density=80, frequency=1, speed=.7):
        '''Render array with beautiful colors'''
        fullImagePath = os.path.join(imagedir, imagefile)
        pixelCount = len(self.allMap)
        colorList = sample_sectors(fullImagePath, pixelCount)
        megaCommand = []
        iterate = 0
        for p in self.allMap:
            color = grbFix(colorList[iterate])
            megaCommand.append([[p, p + 1], color, .5 * speed])
            iterate += 1
        sendMultiCommand(megaCommand, self.controller)
        grouping = density // 20
        while True:
            #Grab some number of pixels
            sampledPix = randomPixels(int(density * randomPercent(50, 150)))
            colorList = sample_sectors(fullImagePath, len(sampledPix))
            iterate = 0
            multiCommand = []
            for pix in sampledPix:
                color = grbFix(colorList[iterate])
                multiCommand.append([[pix, pix + 1], color, 1 / speed])
                if iterate % grouping == 0:
                    sendMultiCommand(multiCommand, self.controller)
                    multiCommand = []
                    time.sleep((.1 / speed) * randomPercent(75, 125))
                iterate += 1
            if frequency:
                time.sleep(frequency * randomPercent(50, 100))

    def fireflyRigid(self, index, colorPrimary, colorSecondary, colorBackground, speed):
        '''Used by fireflies() effect. A single pixel fades up, fades down to a
        different color, and then recedes to background'''
        #Fly fades up to primary color
        upTime = 0
        sendCommand([index, index + 1], colorPrimary, self.controller, fadetime=upTime)
        time.sleep(1.3 / speed)
        #Fly fades down to secondary color
        downTime = 5.0 / speed
        sendCommand([index, index + 1], colorBackground, controller, fadetime=downTime)

    def firefly(self, index, colorPrimary, colorSecondary, colorBackground, speed):
        '''Used by fireflies() effect. A single pixel fades up, fades down to a
        different color, and then recedes to background'''
        #Fly fades up to primary color
        upTime = (.5 * randomPercent(80, 160)) / speed
        sendCommand([index, index + 1], colorPrimary, self.controller, fadetime=upTime)
        time.sleep((1.3 / speed) * randomPercent(80, 160))
        #Fly fades down to secondary color
        downTime = (3.7 * randomPercent(75, 110)) / speed
        sendCommand([index, index + 1], colorSecondary, controller, fadetime=downTime)
        time.sleep((5.0 / speed) * randomPercent(80, 120))
        #Fly recedes into background
        sendCommand([index, index + 1], colorBackground, self.controller, fadetime=.5)

    def fireflies(self, density=7, frequency=5, speed=0.7, colorPrimary=[85,117,0], colorSecondary=[10,26,0], colorBackground=[0,12,22]):
        '''Dots randomly appear on the array, and fade out into a different color'''
        #Establish the background layer
        backgroundLayer = []
        self.room.off()
        patch.fixture('Full Array').setColor(colorBackground)
        #Effect loop
        iteration = 0
        nextChoice = random.randrange(4, 8)
        while True:
            #Grab pixels to put fireflies on
            flyLocations = self.randomPixels(int(density * randomPercent(25, 150)))
            #All flies appear
            for l in flyLocations:
                flyThread = threading.Thread(target=self.firefly, args=[l, colorPrimary, colorSecondary, colorBackground, speed])
                flyThread.start()
                time.sleep((.1 / speed) * randomPercent(100, 250))
            if iteration % nextChoice == 0:
                iteration = 0
                nextChoice = random.randrange(5, 10)
                time.sleep(frequency * randomPercent(50, 110))
            else:
                iteration += 1
                time.sleep((.5 / speed) * randomPercent(90, 190))
            time.sleep((2 / speed) * randomPercent(10, 200))

    def static(self, staticMap, fadeTime, globalBrightness):
        '''User definied fixed look for the room'''

    def gradientLoop(realTime, cycleTime, startTime):
        '''Wraps a cylindrical gradient around the array'''


    def hyperspace(speed, colorPrimary, colorSecondary):
        '''Radial streaks of color move through the space'''

    def shimmer(speed, density, colorSpread, colorPrimary, colorSecondary):
        '''Base color field with flashes of secondary color'''

sunriseGradient = [[[42, 6, 84], 20], [[33, 22, 178], 20], [[126, 28, 255], 20], [[159, 63, 219], 20], [[255, 107, 91], 20], [[255, 179, 93], 20], [[255, 206, 182], 20], [[255, 253, 245], 20]]
sunriseGradient2 = sunriseGradient.copy()
sunriseGradient2.reverse()
sunriseGradient = sunriseGradient + sunriseGradient2
del sunriseGradient2
sunriseGradient = gradientBuilder(sunriseGradient)
