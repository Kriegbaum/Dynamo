''' This is a restructuring of the Dynamo system, fixture functions will now be
class-based because I'm trying to be a civilized person'''

import os
import yaml
import colorsys
import socket
import json
import atexit
from phue import Bridge
import random
import math
import time
from PIL import Image
from PIL import ImageFile
import numpy as np
import threading
import requests

########################Default locations for config files######################
defaultConfigPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user', 'config.yml')
defaultPatchPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user', 'patch.yml')
defaultScenePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user', 'scenes.yml')

########################Basic Socket Functions##################################
#Oour local IP address, tells server where to send data back to
ipSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    ipSock.connect(('10.255.255.255', 1))
    localIP = ipSock.getsockname()[0]
except:
    localIP = '127.0.0.1'
ipSock.close()
socket.setdefaulttimeout(15)

#####################opcBridge Companion Functions##############################
'''The following functions allow direct access to opcBridge or dmxBridge. These
should stay classless to allow finer control for things like effects engines
fixutre class member functions may depend on some of these functions'''

def seaGet(controller, route, params=None):
    if params:
        for p in params:
            params[p] = json.dumps(params[p])
    response = requests.get('http://' + controller.ip + ':' + str(controller.port) + '/' + route, params=params)
    return response.content

def seaPut(controller, route, params=None):
    if params:
        for p in params:
            params[p] = json.dumps(params[p])
    response = requests.put('http://' + controller.ip + ':' + str(controller.port) + '/' + route, params=params)
    return response.content

def requestArbitration(id, controller):
    '''Asks for arbitration from the controller, currently the server makes the
    dcecisions about whether or not you should be in control, returns a bool'''
    arbitration = seaGet(controller, 'arbitration', params={'id': id})
    try:
        arbitration = json.loads(arbitration)
    except:
        print('Arbitration request failed, continuting routine')
        return True
    return arbitration

def setArbitration(id, controller):
    '''Takes arbitration for your own process. An id should be established for
    the routine that calls this function, id should be descriptive of process'''
    seaPut(controller, 'arbitration', params={'id': id})

def multiConstructor(fixture, rgb, fadeTime):
    rgb = fixture.colorCorrect(rgb)
    if fixture.grb:
        rgb = grbFix(rgb)
    return [fixture.indexes, rgb, fadeTime]

def sendMultiCommand(commands, controller):
    '''Sends a command that issues an absoluteFade to multiple fixtures at once
    This should be used every time more than one command is supposed to happen simultaneously
    it is more efficent for opcBridge, faster, and less error prone'''
    #Index 0 in each command can be fixture or index, but should be index by the time it reaches opcBridge
    seaGet(controller, 'multicommand', params={'commandlist': commands})

def sendCommand(indexes, rgb, controller, fadeTime=5):
    '''Sends a dictionary to specified controller'''
    #typical command
    #{'type': 'absoluteFade', 'indexes': [0,512], 'color': [r,g,b], 'fadeTime': 8-bit integer}
    seaGet(controller, 'absolutefade', params={'indexes': indexes, 'rgb': rgb, 'fadetime': fadeTime})

'''The following functions need to be reworked in order to function in the new
structure of this system. They should probably eventually end up as fixture
member functions for fadecandy fixtures, they work well for pixel tape

def rippleFade(fixture, rgb, rippleTime=5, type='wipe'):
    sleepTime = rippleTime / len(fixture.indexes)
    #0.06s currently represents the minimum time between commands that opcBridge can handle on an RPI3
    #if sleepTime < .06:
    #    sleepTime = .06
    for index in fixture.indexes:
        sendCommand([index, index + 1], rgb, fadetime=.9, controller=fixture.controller)
        time.sleep(sleepTime)

def dappleFade(fixture, rgb, fadetime=5):
    indexes = fixture.indexes
    sleepTime = fadetime / len(fixture.indexes)
    #0.06s currently represents the minimum time between commands that opcBridge can handle on an RPI3
    #if sleepTime < .06:
    #    sleepTime = .06
    while indexes:
        index = indexes.pop(random.randrange(0, len(indexes)))
        fadeTime = 1.5 * random.randrange(8, 15) * .1
        sendCommand([index, index + 1], rgb, fadetime=fadetime, controller=fixture.controller)
        time.sleep(sleepTime)
'''

def exitReset(controllerList):
    for c in controllerList:
        setArbitration(False, c)
    print('Releasing arbitration')

def gatherControllers(room):
    controllerList = []
    for l in room:
        if l.system == 'Fadecandy':
            if l.controller not in controllerList:
                controllerList.append(l.controller)
    for c in controllerList:
        setArbitration(True, c)
    atexit.register(exitReset, controllerList)
    return controllerList

def gatherArbitration(controllerList):
    if controllerList:
        for c in controllerList:
            if not requestArbitration(c):
                return False
        return True
    else:
        return True

############################Hue Control Object##################################

def rgbToHue(RGB):
    '''Converts rgb color to the specific format that Hue API uses'''
    #colorsys takes values between 0 and 1, PIL delivers between 0 and 255
    R = RGB[0] / 255
    G = RGB[1] / 255
    B = RGB[2] / 255
    #Makes standard HSV
    hsv = colorsys.rgb_to_hsv(R, G, B)
    #Hue api expresses hue in 16 bit value, thus strange numbers on index 0
    hsv_p = [int(hsv[0] * 360 * 181.33), int(hsv[1] * 255), int(hsv[2] * 255)]
    return hsv_p

def hueToRGB(hsvHue):
    '''Converts values from Philips Hue API to standard RGB'''
    #Phillips Hue lights use a 16 bit value for its hue, thus weird number for index 0 of HSV
    hue = hsvHue[0] / 65278.8
    sat = hsvHue[1] / 255
    val = hsvHue[2] / 255
    rgbTMP = colorsys.hsv_to_rgb(hue, sat, val)
    #Colorsys uses a 0-1 value range, we want 0-255
    rgbTMP = [rgbTMP[0] * 255, rgbTMP[1] * 255, rgbTMP[2] * 255]

    return rgbTMP

#####################Color manipulation functions###############################
def bridgeValues(totalSteps, start, end):
    '''Generator that creates interpolated steps between a start and end value
    Accepts an rgb value, outputs rgb values'''
    newRGB = start
    diffR = (end[0] - start[0]) / float(totalSteps)
    diffG = (end[1] - start[1]) / float(totalSteps)
    diffB = (end[2] - start[2]) / float(totalSteps)
    yield start
    for i in range(totalSteps - 2):
        newRGB = [newRGB[0] + diffR, newRGB[1] + diffG, newRGB[2] + diffB]
        yield [int(newRGB[0]), int(newRGB[1]), int(newRGB[2])]
    yield end

def gradientBuilder(start, end, steps):
    '''Builds an rgb gradient list given the start value, end value, and number
    of steps in between start and end'''
    gradientOut = []
    bridgeGenerator = bridgeValues(steps, start, end)
    for c in range(steps):
        gradientOut.append(next(bridgeGenerator))
    return gradientOut

def gradientApplicator(start, end, indexList, controller, fadeTime=1):
    '''Applies a gradient to a given range of indexes on a given controller'''
    gradientList = gradientBuilder(start, end, len(indexList))
    for index in indexList:
        controller.cache([index], gradientList.pop(0), fadeTime, construct=False)
    controller.multiCommand()

def randomPercent(lower, upper):
    '''Returns a random decimal percent given bounds in integers'''
    return .01 * random.randrange(lower, upper)

def randomRGB():
    '''Generates a random color, good for doing tests on the system'''
    r = random.randrange(0,255)
    g = random.randrange(0,255)
    b = random.randrange(0,255)
    rgb = [r, g, b]
    print('Generated a random color:')
    print(rgb)
    print()
    return rgb

def clamp(value, lower, upper):
    '''Returns lower if value is below bounds, returns upper if above, returns value if inside'''
    return min((max(value, lower), upper))

def grbFix(grb):
    '''returns a grb list as an rgb list, used often with WS2811 bullshit'''
    return [grb[1], grb[0], grb[2]]

def rgbRGBW(rgb):
    '''3 channel color expression to 4 color. Requires testing, maybe not accurate'''
    max = max(rgb)
    rgbwOut = [0,0,0,0]
    #If our light is off, skip the rest of the processing
    if not max:
        return rgbwOut
    #We get luminance here, basically a greyscale representation of the brightness of this color
    multiplier = 255 / max
    hR = rgb[0] * multiplier
    hG = rgb[1] * multiplier
    hB = rgb[3] * multiplier
    M = max(hR, max(hG, hB))
    m = min(hR, min(hG, hB))
    luminance = ((M + m) / 2.0 - 127.5) * (255 / 127.5) / multiplier
    #Our white channel is pure luminance, and can replace some RGB output
    rgbwOut[0] = rgb[0] - luminance
    rgbwOut[1] = rgb[1] - luminance
    rgbwOut[2] = rgb[2] - luminance
    rgbwOut[3] = luminance
    #Make sure we havent created an invalid color
    for i in rgbwOut:
        i = clamp(i, 0, 255)
    return rgbwOut

def cctRGB(kelvin):
    '''Takes a color temperature value and makes it RGB, currently doesnt feel accurate
    This algorithm was found on the internet, additional testing required'''
    outR, outG, outB = 0, 0, 0
    temp = kelvin / 100.0
    if temp <= 66:
        outR = 255
        outG = 99.4708025861 * math.log(temp - 10) - 161.1195681661
        if temp <= 19:
            outB = 0
        else:
            outB = 138.5177312231 * math.log(temp - 10) - 305.0447927307
    else:
        outR = 329.698727446 * math.pow(temp - 60, -0.1332047592)
        outG = 288.1221695283 * math.pow(temp - 60, -0.0755148492)
        outB = 255

    outR = clamp(outR, 0, 255)
    outG = clamp(outG, 0, 255)
    outB = clamp(outB, 0, 255)

    return [outR, outG, outB]

def rgbSetBrightness(setBri, rgb):
    currentBri = max(rgb)
    ratio = setBri / currentBri
    rgbOut = [rgb[0] * ratio, rgb[1] * ratio, rgb[2] * ratio]
    return rgbOut

####################IMAGE MANIPULATION FUNCTIONS################################

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

def sampleSectors(image, count):
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

##################Begin Fixture Patching Process################################

def rangeParser(yamlInput):
    '''Interprets a complex pixel list definition from a list of strings'''
    if type(yamlInput) == int:
        return yamlInput
    elif type(yamlInput) == str:
        rangeTmp = yamlInput.split('-')
        rangeTmp = range(int(rangeTmp[0]), int(rangeTmp[1]) + 1)
        for i in rangeTmp:
            return list(rangeTmp)

def testDict(dictionary, key, default):
    '''See if the patch dictionary has specified a value. If it doesn't, return
    a specificed default'''
    try:
        result = dictionary[key]
        return result
    except KeyError:
        return default

def newLstItem(lst, item):
    '''Checks to see if an item is in a list, if not, adds it'''
    if item not in lst:
        lst.append(item)

class Controller:
    '''Contains addressing information for various types of room controllers'''
    def __init__(self, patchDict):
        self.name = patchDict['name']
        self.room = patchDict['room']
        self.ip = patchDict['ip']
        self.system = patchDict['system']
        self.multiCache = []
        if self.system == 'Fadecandy':
            self.port = testDict(patchDict, 'port', 8000)
        elif self.system == 'CustomRelay':
            self.port = testDict(patchDict, 'port', 8001)
        elif self.system == 'DMX':
            self.port = testDict(patchDict, 'port', 8002)

    def __repr__(self):
        stringOut = self.name
        stringOut += '\nRoom: %s' % self.room
        stringOut += '\nIP: %s' % self.ip
        stringOut += '\nSystem: %s' % self.system
        stringOut += '\nPort: %s' % self.port
        return stringOut

    def getPixels(self):
        '''This will tell you the value of the first index of the fixutre, this
        will not always accurately reflect the state of the whole fixture'''
        response = seaGet(self, 'pixels')
        return json.loads(response)

    def getArbitration(self, id):
        response = seaGet(self, 'arbitration', params={'id':id})
        try:
            arbitration = json.loads(response)
        except:
            print('Error in retrieving Arbitration for %s, continuting routine...' % self)
            return True
        return arbitration

    def setArbitration(self, id):
        seaPut(self, 'arbitration', params={'id':id})

    def cache(self, fixture, color, fadeTime, construct=True):
        '''Stows a command in multiCache, to be cleared by a multicommand'''
        if construct:
            command = multiConstructor(fixture, color, fadeTime)
        else:
            command = [fixture, color, fadeTime]
        self.multiCache.append(command)

    def multiCommand(self):
        '''sends all commands stored in cache'''
        sendMultiCommand(self.multiCache, self)
        self.multiCache = []

class Fixture:
    '''Basic lighting object, can easily push colors to it, get status, and
    other control functions'''
    def __init__(self, patchDict):
        self.name = patchDict['name']
        self.system = patchDict['system']
        self.room = testDict(patchDict, 'room', 'UNUSED')
        self.colorCorrection = testDict(patchDict, 'colorCorrection', [1, 1, 1])
        self.proportion = testDict(patchDict, 'proportion', 1)
        for i in range(len(self.colorCorrection)):
            self.colorCorrection[i] *= self.proportion

    def colorCorrect(self, rgb):
        '''Returns a corrected value for the specific fixture to use, currently
        clamps color output in a linear fashion, but you should investigate a
        solution that involves luminance, because this gets inaccurate at the
        bottom end of the dimming curve'''
        tempList =  [self.colorCorrection[0] * rgb[0],
                    self.colorCorrection[1] * rgb[1],
                    self.colorCorrection[2] * rgb[2]]
        return tempList


class Fadecandy(Fixture):
    '''WS28** control over fadecandy processor. Commands all tie to opcBridge.py
    included in this project. These fixtures are exclusively RGB or GRB'''
    def __init__(self, patch, patchDict):
        Fixture.__init__(self, patchDict)
        self.indexes = []
        for i in patchDict['indexes']:
            temp = rangeParser(i)
            if type(temp) == int:
                self.indexes.append(temp)
            elif type(temp) == list:
                self.indexes += temp
        self.grb = testDict(patchDict, 'grb', False)
        self.controller = patch.controllers[patchDict['controller']]

    def __repr__(self):
        stringOut = self.name
        stringOut += '\nType: %s' % self.system
        stringOut += '\nRoom: %s' % self.room
        stringOut += '\nIndexes: %s - %s' % (self.indexes[0], self.indexes[-1])
        stringOut += '\nController: %s\n' % self.controller.name
        return(stringOut)

    def setColor(self, rgb, fadeTime=.5):
        rgb = self.colorCorrect(rgb)
        if self.grb:
            rgb = grbFix(rgb)
        params = {'rgb': rgb, 'fadetime': fadeTime, 'indexes': self.indexes}
        seaGet(self.controller, 'absolutefade', params=params)

    def getColor(self):
        '''This will tell you the value of the first index of the fixutre, this
        will not always accurately reflect the state of the whole fixture'''
        pixels = seaGet(self.controller, 'pixels')
        pixels = json.loads(pixels)
        return pixels[self.indexes[0]]

    def off(self, fadeTime=0):
        '''Turns the fixture off in specified time'''
        self.setColor([0, 0, 0], fadeTime)

    def on(self, fadeTime=0):
        '''Turns fixture on to default value in specified time,
        does nothing if fixture is already on'''
        #TODO: handle default values for fadecandy fixtures
        if sum(self.getColor()) == 0:
            self.setColor([255, 202, 190], fadeTime)

    def fadeUp(self, magnitude=25, fadeTime=0.5):
        params = {'indexes': self.indexes, 'magnitude': magnitude, 'fadetime': fadeTime}
        seaGet(self.controller, 'relativefade', params=params)

    def fadeDown(self, magnitude=25, fadeTime=0.5):
        params = {'indexes': self.indexes, 'magnitude': magnitude * -1, 'fadetime': fadeTime}
        seaGet(self.controller, 'relativefade', params=params)

class PixelArray(Fixture):
    def __init__(self, patch, patchDict):
        Fixture.__init__(self, patchDict)
        self.indexes = []
        self.strandMap = []
        self.segmentMap = []
        for strand in patchDict['map']:
            strandList = []
            segmentList = []
            for segment in strand:
                indexes = rangeParser(segment)
                segmentList.append(indexes)
                for index in indexes:
                    self.indexes.append(index)
                    strandList.append(index)
            self.segmentMap.append(segmentList)
            self.strandMap.append(strandList)
        self.articulationPoints = 0
        self.articulationPoints += len(self.segmentMap)
        for strand in self.segmentMap:
            self.articulationPoints += len(strand)
        self.controller = patch.controllers[patchDict['controller']]
        self.intersections = testDict(patchDict, 'intersections', [])
        self.grb = testDict(patchDict, 'grb', False)

    def __repr__(self):
        stringOut = self.name
        stringOut += '\nType: %s' % self.system
        stringOut += '\nRoom: %s' % self.room
        stringOut += '\nIndexes: %s - %s' % (self.indexes[0], self.indexes[-1])
        stringOut += '\nController: %s\n' % self.controller.name
        return(stringOut)

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
        '''Returns a list [number] items long of random pixels picked from indexes'''
        pixelList = []
        for i in range(0, number + 1):
            pixelList.append(random.choice(self.indexes))
        return pixelList

    #BASIC FIXTURE FUNCTIONS
    def setColor(self, rgb, fadeTime=.5):
        rgb = self.colorCorrect(rgb)
        if self.grb:
            rgb = grbFix(rgb)
        params = {'rgb': rgb, 'fadetime': fadeTime, 'indexes': self.indexes}
        seaGet(self.controller, 'absolutefade', params=params)

    def getColor(self):
        '''This will tell you the value of the first index of the fixutre, this
        will not always accurately reflect the state of the whole fixture'''
        pixels = seaGet(self.controller, 'pixels')
        pixels = json.loads(pixels)
        return pixels[self.indexes[0]]

    def off(self, fadeTime=0):
        '''Turns the fixture off in specified time'''
        self.setColor([0, 0, 0], fadeTime)

    def on(self, fadeTime=0):
        '''Turns fixture on to default value in specified time,
        does nothing if fixture is already on'''
        #TODO: handle default values for fadecandy fixtures
        if sum(self.getColor()) == 0:
            self.setColor([255, 202, 190], fadeTime)

    def fadeUp(self, magnitude=25, fadeTime=0.5):
        params = {'indexes': self.indexes, 'magnitude': magnitude, 'fadetime': fadeTime}
        seaGet(self.controller, 'relativefade', params=params)

    def fadeDown(self, magnitude=25, fadeTime=0.5):
        params = {'indexes': self.indexes, 'magnitude': magnitude * -1, 'fadetime': fadeTime}
        seaGet(self.controller, 'relativefade', params=params)

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

    def imageSample(self, imagedir, imagefile, density=80, frequency=1, speed=1):
        '''Render array with beautiful colors'''
        self.controller.setArbitration('strandImageSample')
        fullImagePath = os.path.join(imagedir, imagefile)
        pixelCount = len(self.indexes)
        colorList = sampleSectors(fullImagePath, pixelCount)
        megaCommand = []
        iterate = 0
        for p in self.indexes:
            color = self.colorCorrect(colorList[iterate])
            if self.grb:
                color = grbFix(color)
            megaCommand.append([[p], color, .5 * speed])
            iterate += 1
        sendMultiCommand(megaCommand, self.controller)
        grouping = density // 20
        while True:
            if self.controller.getArbitration('strandImageSample'):
                #Grab some number of pixels
                sampledPix = self.randomPixels(int(density * randomPercent(50, 150)))
                colorList = sampleSectors(fullImagePath, len(sampledPix))
                iterate = 0
                multiCommand = []
                for pix in sampledPix:
                    color = self.colorCorrect(colorList[iterate])
                    if self.grb:
                        color = grbFix(color)
                    multiCommand.append([[pix], color, 1 / speed])
                    if iterate % grouping == 0:
                        sendMultiCommand(multiCommand, self.controller)
                        multiCommand = []
                        time.sleep((.1 / speed) * randomPercent(75, 190))
                    iterate += 1
                if frequency:
                    time.sleep(frequency * randomPercent(50, 110))
            else:
                print('Routine halted, overriden by manual event')
                break

    def fireflyRigid(self, index, colorPrimary, colorSecondary, colorBackground, speed):
        '''Used by fireflies() effect. A single pixel fades up, fades down to a
        different color, and then recedes to background'''
        #Fly fades up to primary color
        upTime = 0
        sendCommand([index], colorPrimary, self.controller, fadeTime=upTime)
        time.sleep(1.3 / speed)
        #Fly fades down to secondary color
        downTime = 5.0 / speed
        sendCommand([index], colorBackground, controller, fadeTime=downTime)

    def firefly(self, index, colorPrimary, colorSecondary, colorBackground, speed):
        '''Used by fireflies() effect. A single pixel fades up, fades down to a
        different color, and then recedes to background'''
        #Fly fades up to primary color
        upTime = (.5 * randomPercent(80, 160)) / speed
        sendCommand([index], colorPrimary, self.controller, fadeTime=upTime)
        time.sleep((1.3 / speed) * randomPercent(80, 160))
        #Fly fades down to secondary color
        downTime = (3.7 * randomPercent(75, 110)) / speed
        sendCommand([index], colorSecondary, self.controller, fadeTime=downTime)
        time.sleep((5.0 / speed) * randomPercent(80, 120))
        #Fly recedes into background
        sendCommand([index], colorBackground, self.controller, fadeTime=.5)

    def fireflies(self, density=7, frequency=5, speed=0.7, colorPrimary=[85,117,0], colorSecondary=[10,26,0], colorBackground=[0,12,22]):
        '''Dots randomly appear on the array, and fade out into a different color'''
        colorPrimary = self.colorCorrect(colorPrimary)
        colorSecondary = self.colorCorrect(colorSecondary)
        colorBackground = self.colorCorrect(colorBackground)
        #Establish the background layer
        backgroundLayer = []
        self.setColor([0,24,44])
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

    def gradientLoop(self, realTime, cycleTime, startTime):
        '''Wraps a cylindrical gradient around the array'''


    def hyperspace(self, speed, colorPrimary, colorSecondary):
        '''Radial streaks of color move through the space'''

    def shimmer(self, speed, density, colorSpread, colorPrimary, colorSecondary):
        '''Base color field with flashes of secondary color'''

    def rollFade(self, rgb, fadeTime, forward=True):
        '''Rolls a color down the array'''
        rgb = self.colorCorrect(rgb)
        if self.grb:
            rgb = grbFix(rgb)
        lowTime = fadeTime * 0.3
        interval = (fadeTime - lowTime) / len(self.strandMap)
        if forward:
            for strand in self.strandMap:
                stepTime = lowTime
                for pixel in strand:
                    self.controller.cache([pixel], rgb, stepTime, construct=False)
                    stepTime += interval
        else:
            for strand in self.strandMap[::-1]:
                stepTime = lowTime
                for pixel in strand:
                    self.controller.cache([pixel], rgb, stepTime, construct=False)
                    stepTime += interval
        self.controller.multiCommand()



class Hue(Fixture):
    '''Expensive phillips hue fixtures. Can be color or just white, all of these
    communicate through the pHue library and use a bridge on the network'''
    def __init__(self, patch, patchDict):
        Fixture.__init__(self, patchDict)
        self.color = testDict(patchDict, 'color', True)
        self.id = testDict(patchDict, 'id', 0)
        self.hueBridge = patch.hueBridge

    def __repr__(self):
        stringOut = ''
        stringOut += self.name
        stringOut += '\nType: %s' % self.system
        stringOut += '\nRoom: %s' % self.room
        stringOut += '\nID: %s\n' % self.id
        return(stringOut)

    def setColor(self, rgb, fadeTime=.5):
        rgb = self.colorCorrect(rgb)
        rgb = rgbToHue(rgb)
        command = {'hue': rgb[0], 'sat': rgb[1], 'bri': rgb[2], 'transitiontime': int(fadeTime * 10), 'on': True}
        if rgb == [0, 0, 0]:
            command['on'] = False
        self.hueBridge.set_light(self.id, command)

    def off(self, fadeTime=0):
        fadeTime = int(fadeTime)
        command = {'on': False, 'transitiontime': fadeTime * 10}
        self.hueBridge.set_light(self.id, command)

    def on(self, fadeTime=0):
        if not self.hueBridge.get_light(self.id, 'on'):
            self.setColor([255, 202, 190])

    def getColor(self):
        if not self.hueBridge.get_light(self.id, 'on'):
            return False
        hue = self.hueBridge.get_light(self.id, 'hue')
        sat = self.hueBridge.get_light(self.id, 'sat')
        val = self.hueBridge.get_light(self.id, 'bri')

        rgb = hueToRGB([hue, sat, val])

        return rgb

    def fadeUp(self, amount=25):
        if not self.hueBridge.get_light(self.id, 'on'):
            return False
        currentBri = self.hueBridge.get_light(self.id, 'bri')
        currentBri += amount
        currentBri = clamp(currentBri, 0, 255)
        command = {'bri': currentBri}
        self.hueBridge.set_light(self.id, command)

    def fadeDown(self, amount=25):
        if not self.hueBridge.get_light(self.id, 'on'):
            return False
        currentBri = self.hueBridge.get_light(self.id, 'bri')
        currentBri -= amount
        currentBri = clamp(currentBri, 0, 255)
        command = {'bri': currentBri}
        self.hueBridge.set_light(self.id, command)


class DMX(Fixture):
    '''DMX gateway control, communicates with dmxBridge.py included in this
    project. DMX fixtures can be RGB, RGBW, and anything else out there'''
    pass

class Relay:
    '''Simple on/off power control, used for stereo control or power saving'''
    def __init__(self, patchDict):
        self.name = patchDict['name']
        self.system = patchDict['system']
        self.room = testDict(patchDict, 'room', 'UNUSED')
        self.essential = testDict(patchDict, 'essential', True)
        self.stage = testDict(patchDict, 'stage', 1)

class CustomRelay(Relay):
    '''Custom built relay box, communicates with relayBridge.py for control'''
    def __init__(self, patch, patchDict):
        Relay.__init__(self, patchDict)
        self.index = patchDict['index']
        self.controller = patch.controllers[patchDict['controller']]

    def __repr__(self):
        stringOut = self.name
        stringOut += '\nType: %s' % self.system
        stringOut += '\nRoom: %s' % self.room
        stringOut += '\nIndex: %s' % self.index
        stringOut += '\nStage: %s' % self.stage
        stringOut += '\nController: %s\n' % self.controller.name
        return(stringOut)

    def getState(self):
        params = {'index': self.index}
        response = seaGet(self, 'state', params=params)
        return json.loads(response)

    def on(self):
        params = {'index': self.index, 'state': True}
        seaGet(self, 'switch', params=params)

    def off(self):
        params = {'index': self.index, 'state': False}
        seaGet(self, 'switch', params=params)

    def toggle(self):
        params = {'index': self.index}
        seaGet(self, 'toggle', params=params)

class HueRelay(Relay):
    '''Hue system relay, uses different communication method, but functionally
    the same'''
    def __init__(self, patch, patchDict):
        Relay.__init__(self, patchDict)
        self.id = patchDict['id']
        self.hueBridge = patch.hueBridge

    def __repr__(self):
        stringOut = self.name
        stringOut += '\nType: %s' % self.system
        stringOut += '\nRoom: %s' % self.room
        stringOut += '\nID: %s' % self.id
        stringOut += '\nStage %s' % self.stage
        return(stringOut)

    def getState(self):
        return self.hueBridge.get_light(self.id, 'on')

    def on(self):
        self.hueBridge.set_light(self.id, {'on': True})

    def off(self):
        self.hueBridge.set_light(self.id, {'on': False})

    def toggle(self):
        state = self.getState()
        if state:
            self.off()
        else:
            self.on()

class Room:
    '''Basic control groups, makes controlling a number of fixtures easy'''
    def __init__(self, name, fixtureList, relayList):
        self.name = name
        self.fixtureList = fixtureList
        self.relayList = relayList
        self.controllerList = []
        if len(relayList) > 0:
            self.stages = max([x.stage for x in relayList])
        for f in fixtureList:
            if hasattr(f, 'controller'):
                if f.controller not in self.controllerList:
                    self.controllerList.append(f.controller)
        for r in relayList:
            if hasattr(r, 'controller'):
                if r.controller not in self.controllerList:
                    self.controllerList.append(r.controller)

    def __repr__(self):
        stringOut = 'Name: %s' % self.name
        stringOut += '\nFixtures:'
        if not self.fixtureList:
            stringOut += '\n  NONE'
        else:
            for f in self.fixtureList:
                stringOut += '\n  %s' % f.name
        stringOut += '\nRelays:'
        if not self.relayList:
            stringOut += '\n  NONE'
        else:
            for r in self.relayList:
                stringOut += '\n  %s' % r.name
        stringOut += '\nControllers:'
        if not self.controllerList:
            stringOut += '\n  NONE'
        else:
            for c in self.controllerList:
                stringOut += '\n  %s' % c.name
        stringOut += '\n'
        return(stringOut)

    def setColor(self, rgb, fadeTime=0.5):
        for f in self.fixtureList:
            if hasattr(f, 'controller'):
                f.controller.cache(f, rgb, fadeTime)
            else:
                f.setColor(rgb, fadeTime)
        for c in self.controllerList:
            c.multiCommand()

    def off(self, fadeTime=0):
        for f in self.fixtureList:
            f.off(fadeTime)

    def on(self, fadeTime=0):
        for f in self.fixtureList:
            f.on()

    def fadeUp(self, amount=25):
        for f in self.fixtureList:
            f.fadeUp(amount)

    def fadeDown(self, amount=25):
        for f in self.fixtureList:
            f.fadeDown(amount)

    def relaysOn(self):
        for i in range(1, self.stages + 1):
            for r in self.relayList:
                if r.stage == i:
                    r.on()
            time.sleep(3)

    def relaysOff(self):
        for i in range(self.stages, 0, -1):
            for r in self.relayList:
                if r.stage == i:
                    r.off()
            time.sleep(2)

    def relaysToggle(self):
        roomState = True
        for r in self.relayList:
            if not r.getState():
                roomState = False
        if roomState:
            self.relaysOff()
        else:
            self.relaysOn()

    def allOn(self):
        for f in self.fixtureList:
            f.on()
        self.relaysOn()

    def allOff(self):
        for f in self.fixtureList:
            f.off()
        self.relaysOff()

    def scene(self, sceneDict, fadeTime=1):
        '''A scene can be defined in two ways, keys are fixture names, and values
        are either an rgb list, or an rgb list and a specified fadetime for that fixture'''
        for s in sceneDict:
            if type(sceneDict[s]) == list:
                sceneDict[s] = {'color': sceneDict[s], 'time': fadeTime}
        for f in self.fixtureList:
            if f.name in sceneDict:
                color = sceneDict[f.name]['color']
                timing = sceneDict[f.name]['time']
                if hasattr(f, 'controller'):
                    f.controller.cache(f, color, timing)
                else:
                    f.setColor(color, timing)
        for c in self.controllerList:
            c.multiCommand()

    def setArbitration(self, id):
        for c in self.controllerList:
            c.setArbitration(id)

    def getArbitration(self, id):
        result = True
        for c in self.controllerList:
            if not c.getArbitration(id):
                result = False
        return result

class Patch:
    '''Creates an object from which we can access all of our fixtures and rooms'''
    def __init__(self, configPath=defaultConfigPath, patchPath=defaultPatchPath):
        #Load in config file
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user', 'config.yml')) as f:
            configFile = f.read()
        configs = yaml.safe_load(configFile)
        #Load in patch file
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user', 'patch.yml')) as f:
            patchFile = f.read()
        patch = yaml.safe_load(patchFile)
        #Load in scenes
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user', 'scenes.yml')) as f:
            sceneFile = f.read()

        self.scenes = yaml.safe_load(sceneFile)
        self.controllers = {}
        self.fixtures = {}
        self.relays = {}
        self.rooms = {}
        self.hueBridge = Bridge(configs['hueIP'])

        roomNames = []

        for c in configs['controllers']:
            new = Controller(configs['controllers'][c])
            self.controllers[new.name] = new

        for f in patch:
            if patch[f]['system'] == 'Fadecandy':
                new = Fadecandy(self, patch[f])
                self.fixtures[new.name] = new
                newLstItem(roomNames, new.room)
            elif patch[f]['system'] == 'Hue':
                new = Hue(self, patch[f])
                self.fixtures[new.name] = new
                newLstItem(roomNames, new.room)
            elif patch[f]['system'] == 'DMX':
                new = DMX(self, patch[f])
                self.fixtures[new.name] = new
                newLstItem(roomNames, new.room)
            elif patch[f]['system'] == 'HueRelay':
                new = HueRelay(self, patch[f])
                self.relays[new.name] = new
                newLstItem(roomNames, new.room)
            elif patch[f]['system'] == 'CustomRelay':
                new = CustomRelay(self, patch[f])
                self.relays[new.name] = new
                newLstItem(roomNames, new.room)
            elif patch[f]['system'] == 'PixelArray':
                new = PixelArray(self, patch[f])
                self.fixtures[new.name] = new
                newLstItem(roomNames, new.room)

        for r in roomNames:
            fixtureList = [self.fixtures[f] for f in self.fixtures if self.fixtures[f].room == r]
            relayList = [self.relays[f] for f in self.relays if self.relays[f].room == r]
            new = Room(r, fixtureList, relayList)
            self.rooms[new.name] = new

        self.rooms['all'] = Room('all', [self.fixtures[f] for f in self.fixtures], [self.relays[r] for r in self.relays])

    def fixture(self, name):
        return self.fixtures[name]

    def relay(self, name):
        return self.relays[name]

    def room(self, name):
        return self.rooms[name]

    def controller(self, name):
        return self.controllers[name]
