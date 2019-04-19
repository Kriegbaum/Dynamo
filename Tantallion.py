''' This is a restructuring of the Dynamo system, fixture functions will now be
class-based because I'm trying to be a civilized person'''

import os
import yaml
import sys
import colorsys
import socket
import json
import atexit
from phue import Bridge
import random

##########################Load Config###########################################
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user', 'config.yml')) as f:
    configFile = f.read()
configs = yaml.load(configFile)

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

def transmit(command, controller):
    '''Takes a command dictionary and a controller, and sockets that command out'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (controller.ip, controller.txPort)
    sock.connect(server_address)
    message = json.dumps(command)
    try:
        sock.sendall(message.encode())
    except Exception as e:
        if type(e) == socket.timeout:
            print('Socket timed out, attempting connection again')
        else:
            print('Sending ' + command['type'] + ' failed')
            print(e)
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

def recieve(controller):
    '''Waits for a response fom a controller that we've sent a request to'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (localIP, controller.rxPort)
    sock.bind(server_address)
    sock.listen(1)
    connection, client_address = sock.accept()
    message = ''
    while True:
        data = connection.recv(16).decode()
        message += data
        if data:
            pass
        else:
            return message
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()

#####################opcBridge Companion Functions##############################
'''The following functions allow direct access to opcBridge or dmxBridge. These
should stay classless to allow finer control for things like effects engines
fixutre class member functions may depend on some of these functions'''

def requestArbitration(id, controller):
    '''Asks for arbitration from the controller, currently the server makes the
    dcecisions about whether or not you should be in control, returns a bool'''
    transmit({'type': 'requestArbitration', 'id': id}, controller)
    arbitration = recieve(controller)
    arbitration = json.loads(arbitration)
    return arbitration

def setArbitration(id, controller):
    '''Takes arbitration for your own process. An id should be established for
    the routine that calls this function, id should be descriptive of process'''
    transmit({'type': 'setArbitration', 'id': id}, controller)

def sendMultiCommand(commands, controller):
    '''Sends a command that issues an absoluteFade to multiple fixtures at once
    This should be used every time more than one command is supposed to happen simultaneously
    it is more efficent for opcBridge, faster, and less error prone'''
    #('type': 'multiCommand', 'commands': [[fixture1, rgb1, fadeTime1], [fixture2, rgb2, fadeTime2]])
    #Index 0 in each command can be fixture or index, but should be index by the time it reaches opcBridge
    command = {'type':'multiCommand', 'commands':commands}
    transmit(command, controller)

def sendCommand(indexrange, rgb, controller, fadetime=5, type='absoluteFade'):
    '''Sends a dictionary to specified controller'''
    #typical command
    #{'type': 'absoluteFade', 'index range': [0,512], 'color': [r,g,b], 'fade time': 8-bit integer}
    command = {'type':'absoluteFade', 'color':rgb, 'fade time': fadetime, 'index range': indexrange}
    transmit(command, controller)

'''The following functions need to be reworked in order to function in the new
structure of this system. They should probably eventually end up as fixture
member functions for fadecandy fixtures, they work well for pixel tape

def rippleFade(fixture, rgb, rippleTime=5, type='wipe'):
    sleepTime = rippleTime / (fixture.indexrange[1] - fixture.indexrange[0])
    #0.06s currently represents the minimum time between commands that opcBridge can handle on an RPI3
    #if sleepTime < .06:
    #    sleepTime = .06
    for index in range(fixture.indexrange[0], fixture.indexrange[1]):
        sendCommand([index, index + 1], rgb, fadetime=.9, controller=fixture.controller)
        time.sleep(sleepTime)

def dappleFade(fixture, rgb, fadetime=5):
    indexes = list(range(fixture.indexrange[0], fixture.indexrange[1]))
    sleepTime = fadetime / (fixture.indexrange[1] - fixture.indexrange[0])
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

#Establish our hue bridge as an object
hueIP = configs['hueIP']
hueBridge = Bridge(hueIP)

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

##################Begin Fixture Patching Process################################

roomDict = {'all': {'fixtures': [], 'relays': []}}
fixtureDict = {}

def testDict(dictionary, key, default):
    '''See if the patch dictionary has specified a value. If it doesn't, return
    a specificed default'''
    try:
        result = dictionary[key]
        return result
    except KeyError:
        return default

class Controller:
    '''Contains addressing information for various types of room controllers'''
    def __init__(self, patchDict):
        self.name = patchDict['name']
        self.room = patchDict['room']
        self.ip = patchDict['ip']
        self.system = patchDict['system']
        if self.system == 'Fadecandy':
            self.txPort = testDict(patchDict, 'txPort', 8000)
            self.rxPort = testDict(patchDict, 'rxPort', 8800)
        elif self.system == 'CustomRelay':
            self.txPort = testDict(patchDict, 'txPort', 8001)
            self.rxPort = testDict(patchDict, 'rxPort', 8801)
        elif self.system == 'DMX':
            self.txPort = testDict(patchDict, 'txPort', 8002)
            self.rxPort = testDict(patchDict, 'rxPort', 8802)

    def __repr__(self):
        stringOut = self.name
        stringOut += '\nRoom: %s' % self.room
        stringOut += '\nIP: %s' % self.ip
        stringOut += '\nSystem: %s' % self.system
        stringOut += '\nTx Port: %s' % self.txPort
        stringOut += '\nRx Port: %s\n' % self.rxPort
        return stringOut

    def requestArbitration(self, id):
        transmit({'type': 'requestArbitration', 'id': id}, self)
        arbitration = recieve(self)
        arbitration = json.loads(arbitration)
        return arbitration

    def setArbitration(self, id):
        transmit({'type': 'setArbitration', 'id': id}, self)

#We roll all controllers declared in config.yml into a dictionary so we can address them by name
controllerDict = {}
for c in configs['controllers']:
    new = Controller(configs['controllers'][c])
    controllerDict[new.name] = new



class Fixture:
    '''Basic lighting object, can easily push colors to it, get status, and
    other control functions'''
    def __init__(self, patchDict):
        self.name = patchDict['name']
        self.system = patchDict['system']
        self.room = testDict(patchDict, 'room', 'UNUSED')
        self.colorCorrection = testDict(patchDict, 'colorCorrection', [1, 1, 1])

        #Get us a directory of fixtures by name
        fixtureDict[self.name] = self

        #Get us a directory of fixutres by room
        if self.room in roomDict:
            roomDict[self.room]['fixtures'].append(self)
        else:
            roomDict[self.room] = {}
            roomDict[self.room]['fixtures'] = [self]
        roomDict['all']['fixtures'].append(self)

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
    def __init__(self, patchDict):
        Fixture.__init__(self, patchDict)
        self.indexRange = testDict(patchDict, 'indexrange', [0,0])
        self.grb = testDict(patchDict, 'grb', False)
        self.controller = controllerDict[patchDict['controller']]

    def __repr__(self):
        stringOut = self.name
        stringOut += '\nType: %s' % self.system
        stringOut += '\nRoom: %s' % self.room
        stringOut += '\nIndexes: %s' % self.indexRange
        stringOut += '\nController: %s\n' % self.controller.name
        return(stringOut)

    def setColor(self, rgb, fadeTime):
        rgb = self.colorCorrect(rgb)
        if self.grb:
            rgb = grbFix(rgb)
        command = {'type': 'absoluteFade', 'color': rgb, 'fade time': fadeTime, 'index range': self.indexRange}
        transmit(command, self.controller)

    def returnCommand(self, rgb, fadeTime):
        '''Generates the command needed to set color for this fixutre, called by
        a room function to build a multiCommand for the server'''
        rgb = self.colorCorrect(rgb)
        if self.grb:
            rgb = grbFix(rgb)
        command = {'type': 'absoluteFade', 'color': rgb, 'fade time': fadeTime, 'index range': self.indexRange}
        return command

    def off(self, fadeTime=0):
        '''Turns the fixture off in specified time'''
        self.setColor([0, 0, 0], fadeTime)

    def on(self, fadeTime=0):
        '''Turns fixture on to default value in specified time'''
        #TODO: handle default values for fadecandy fixtures
        pass

    def getColor(self):
        '''This will tell you the value of the first index of the fixutre, this
        will not always accurately reflect the state of the whole fixture'''
        command = {'type': 'pixelRequest'}
        transmit(command, self.controller)
        pixels = json.loads(recieve(self.controller))
        return pixels[self.indexRange[0]]

    def fadeUp(self, amount, fadeTime=0.5):
        command = {'type': 'relativeFade', 'index range': self.indexRange, 'magnitude': amount, 'fade time': fadeTime}
        transmit(command, self.controller)

    def fadeDown(self, amount, fadeTime=0.5):
        command = {'type': 'relativeFade', 'index range': self.indexRange, 'magnitude': amount * -1, 'fade time': fadeTime}
        transmit(command, self.controller)

class Hue(Fixture):
    '''Expensive phillips hue fixtures. Can be color or just white, all of these
    communicate through the pHue library and use a bridge on the network'''
    def __init__(self, patchDict):
        Fixture.__init__(self, patchDict)
        self.color = testDict(patchDict, 'color', True)
        self.id = testDict(patchDict, 'id', 0)

    def __repr__(self):
        stringOut = ''
        stringOut += self.name
        stringOut += '\nType: %s' % self.system
        stringOut += '\nRoom: %s' % self.room
        stringOut += '\nID: %s\n' % self.id
        return(stringOut)

    def setColor(self, rgb, fadeTime):
        rgb = self.colorCorrect(rgb)
        rgb = rgbToHue(rgb)
        command = {'hue': rgb[0], 'sat': rgb[1], 'bri': rgb[2], 'transitiontime': int(fadeTime * 10), 'on': True}
        if rgb == [0, 0, 0]:
            command['on'] = False
        hueBridge.set_light(self.id, command)

    def off(self, fadeTime=0):
        command = {'on': False, 'transitiontime': fadeTime * 10}
        hueBridge.set_light(self.id, command)

    def on(self, fadeTime=0):
        command = {'on': True, 'transitiontime': fadeTime * 10}
        hueBridge.set_light(self.id, command)

    def getColor(self):
        if not hueBridge.get_light(self.id, 'on'):
            return False
        hue = hueBridge.get_light(self.id, 'hue')
        sat = hueBridge.get_light(self.id, 'sat')
        val = hueBridge.get_light(self.id, 'bri')

        rgb = hueToRGB([hue, sat, val])

        return rgb

    def fadeUp(self, amount):
        if not hueBridge.get_light(self.id, 'on'):
            return False
        currentBri = hueBridge.get_light(self.id, 'bri')
        currentBri += amount
        currentBri = clamp(currentBri, 0, 255)
        command = {'bri': currentBri}
        hueBridge.set_light(self.id, command)

    def fadeDown(self, amount):
        if not hueBridge.get_light(self.id, 'on'):
            return False
        currentBri = hueBridge.get_light(self.id, 'bri')
        currentBri -= amount
        currentBri = clamp(currentBri, 0, 255)
        command = {'bri': currentBri}
        hueBridge.set_light(self.id, command)


class DMX(Fixture):
    '''DMX gateway control, communicates with dmxBridge.py included in this
    project. DMX fixtures can be RGB, RGBW, and anything else out there'''
    pass




class Relay:
    '''Simple on/off power control, used for stereo control or power saving'''
    pass

class CustomRelay(Relay):
    '''Custom built relay box, communicates with relayBridge.py for control'''
    pass

class HueRelay(Relay):
    '''Hue system relay, uses different communication method, but functionally
    the same'''
    pass


class Room:
    '''Basic control groups, makes controlling a number of fixtures easy'''
    def __init__(self, name, fixtureList, relayList):
        self.name = name
        self.fixtureList = fixtureList
        self.relayList = relayList
        self.controllerList = []
        for f in fixtureList:
            if f.system == 'Fadecandy' or f.system == 'DMX':
                if f.controller not in self.controllerList:
                    self.controllerList.append(f.controller)
        for r in relayList:
            if r.system == 'CustomRelay':
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

    def setColor(self, rgb, fadeTime):
        for f in self.fixtureList:
            f.setColor(rgb, fadeTime)

    def off(self, fadeTime=0):
        for f in self.fixtureList:
            f.off()

    def on(self, fadeTime=0):
        for f in self.fixtureList:
            f.on()

    def fadeUp(self, amount):
        for f in self.fixtureList:
            f.fadeUp(amount)

    def fadeDown(self, amount):
        for f in self.fixtureList:
            f.fadeDown(amount)

    def scene(self, sceneDict, fadeTime=2):
        '''A scene can be defined in two ways, keys are fixture names, and values
        are either an rgb list, or an rgb list and a specified fadetime for that fixture'''
        for f in sceneDict:
            if len(sceneDict[f]) == 2:
                fixtureDict[f].setColor(sceneDict[f][0], sceneDict[f][1])
            else:
                fixtureDict[f].setColor(sceneDict[f], fadeTime)

    def setArbitration(id):
        pass

    def getArbitration():
        pass

###########################Load Patch###########################################
#Initiate object conaining our patch
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user', 'patch.yml')) as f:
    patchFile = f.read()
patch = yaml.load(patchFile)
#Initialize an object for every fixture declared in patch, place in dictionary so we can reference by name
for f in patch:
    if patch[f]['system'] == 'Fadecandy':
        new = Fadecandy(patch[f])
    elif patch[f]['system'] == 'Hue':
        new = Hue(patch[f])
    elif patch[f]['system'] == 'DMX':
        new = DMX(patch[f])
#We are going to repurpose roomDict, but roomList is a temporary holding pen for the follwing info
roomList = []
for r in roomDict:
    if 'fixtures' in roomDict[r]:
        fixtureList = roomDict[r]['fixtures']
    else:
        fixtureList = []
    if 'relays' in roomDict[r]:
        relayList = roomDict[r]['relays']
    else:
        relayList = []
    new = Room(r, fixtureList, relayList)
    roomList.append(new)
#Roll rooms into a dictionary so we can reference them by name
roomDict = {}
for r in roomList:
    roomDict[r.name] = r

#Initiate scene dictionary for later use
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user', 'scenes.yml')) as f:
    sceneFile = f.read()
scenes = yaml.load(sceneFile)