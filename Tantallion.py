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
import math

########################Basic Socket Functions##################################

#Oour local IP address, tells server where to send data back to
ipSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    ipSock.connect(('255.255.255.255', 1))
    localIP = ipSock.getsockname()[0]
except:
    localIP = '127.0.0.1'
ipSock.close()
socket.setdefaulttimeout(15)

def transmit(command, controller):
    '''Takes a command dictionary and a controller, and sockets that command out'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (controller.ip, controller.txPort)
    message = json.dumps(command)
    sock.connect(server_address)
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

def multiConstructor(fixture, rgb, fadeTime):
    rgb = fixture.colorCorrect(rgb)
    if fixture.grb:
        rgb = grbFix(rgb)
    return [fixture.indexRange, rgb, fadeTime]

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
    #{'type': 'absoluteFade', 'indexRange': [0,512], 'color': [r,g,b], 'fadeTime': 8-bit integer}
    command = {'type':'absoluteFade', 'color':rgb, 'fadeTime': fadetime, 'indexRange': indexrange}
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

def rgbSetBrightness(setBri, rgb):
    currentBri = max(rgb)
    ratio = setBri / currentBri
    rgbOut = [rgb[0] * ratio, rgb[1] * ratio, rgb[2] * ratio]
    return rgbOut


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

    def getArbitration(self, id):
        transmit({'type': 'getArbitration', 'id': id}, self)
        arbitration = recieve(self)
        arbitration = json.loads(arbitration)
        return arbitration

    def setArbitration(self, id):
        transmit({'type': 'setArbitration', 'id': id}, self)

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
        self.indexRange = testDict(patchDict, 'indexrange', [0,0])
        self.grb = testDict(patchDict, 'grb', False)
        self.controller = patch.controllers[patchDict['controller']]

    def __repr__(self):
        stringOut = self.name
        stringOut += '\nType: %s' % self.system
        stringOut += '\nRoom: %s' % self.room
        stringOut += '\nIndexes: %s' % self.indexRange
        stringOut += '\nController: %s\n' % self.controller.name
        return(stringOut)

    def setColor(self, rgb, fadeTime=.5):
        rgb = self.colorCorrect(rgb)
        if self.grb:
            rgb = grbFix(rgb)
        command = {'type': 'absoluteFade', 'color': rgb, 'fadeTime': fadeTime, 'indexRange': self.indexRange}
        transmit(command, self.controller)

    def returnCommand(self, rgb, fadeTime):
        '''Generates the command needed to set color for this fixutre, called by
        a room function to build a multiCommand for the server'''
        rgb = self.colorCorrect(rgb)
        if self.grb:
            rgb = grbFix(rgb)
        command = {'type': 'absoluteFade', 'color': rgb, 'fadeTime': fadeTime, 'indexRange': self.indexRange}
        return command

    def getColor(self):
        '''This will tell you the value of the first index of the fixutre, this
        will not always accurately reflect the state of the whole fixture'''
        command = {'type': 'getPixels'}
        transmit(command, self.controller)
        pixels = json.loads(recieve(self.controller))
        return pixels[self.indexRange[0]]

    def off(self, fadeTime=0):
        '''Turns the fixture off in specified time'''
        self.setColor([0, 0, 0], fadeTime)

    def on(self, fadeTime=0):
        '''Turns fixture on to default value in specified time,
        does nothing if fixture is already on'''
        #TODO: handle default values for fadecandy fixtures
        if sum(self.getColor()) == 0:
            self.setColor([255, 202, 190], fadeTime)

    def fadeUp(self, amount=25, fadeTime=0.5):
        command = {'type': 'relativeFade', 'indexRange': self.indexRange, 'magnitude': amount, 'fadeTime': fadeTime}
        transmit(command, self.controller)

    def fadeDown(self, amount=25, fadeTime=0.5):
        command = {'type': 'relativeFade', 'indexRange': self.indexRange, 'magnitude': amount * -1, 'fadeTime': fadeTime}
        transmit(command, self.controller)

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
    def __init__(self, patchDict):
        Relay.__init__(self, patchDict)
        self.index = patchDict['index']
        self.controller = controllerDict[patchDict['controller']]

    def __repr__(self):
        stringOut = self.name
        stringOut += '\nType: %s' % self.system
        stringOut += '\nRoom: %s' % self.room
        stringOut += '\nIndex: %s' % self.index
        stringOut += '\nController: %s\n' % self.controller.name
        return(stringOut)

    def getState(self):
        pass

    def on(self):
        pass

    def off(self):
        pass

    def toggle(self):
        pass

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
            f.off()

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
            time.sleep(2)

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




##########################Load Config###########################################
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user', 'config.yml')) as f:
    configFile = f.read()
defaultConfigs = yaml.safe_load(configFile)


###########################Load Patch###########################################
#Initiate object conaining our fixture patch
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user', 'patch.yml')) as f:
    patchFile = f.read()
defaultPatch = yaml.safe_load(patchFile)

#Initiate scene dictionary for later use
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user', 'scenes.yml')) as f:
    sceneFile = f.read()
scenes = yaml.safe_load(sceneFile)



class Patch:
    '''Creates an object from which we can access all of our fixtures and rooms'''
    def __init__(self, configs=defaultConfigs, patch=defaultPatch):
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
