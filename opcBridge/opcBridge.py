import opc
import time
import os
import socket
import json
import threading
import queue
import datetime
import numpy as np
import yaml
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
import logging
import requests

#########################LOAD IN USER CONFIG####################################
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'opcConfig.yml')) as f:
    configFile = f.read()
configs = yaml.safe_load(configFile)

################################FLASK OBJECTS###################################
FLASK_DEBUG = False
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
fetcher = Flask(__name__)
api = Api(fetcher)
parser = reqparse.RequestParser()

#########################VARIOUS COMMAND FIELDS#################################
parser.add_argument('fadetime', type=float, help='How long will this fade take?')
parser.add_argument('indexes', type=json.loads, help='Which pixels are targeted')
parser.add_argument('id', type=str, help='Arbtration ID')
parser.add_argument('ip', type=str, help='IP address of client')
parser.add_argument('rgb', type=json.loads, help='Target color')
parser.add_argument('magnitude', type=float, help='Size of fade')
parser.add_argument('commandlist', type=json.loads, help='List of commands for a multicommand')

##########################GET LOCAL IP##########################################
ipSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    ipSock.connect(('10.255.255.255', 1))
    localIP = ipSock.getsockname()[0]
    print('Local IP set to', localIP)
except Exception as e:
    print(e)
    print('Local IP detection failed, listening on localhost')
    localIP = '127.0.0.1'
ipSock.close()
socket.setdefaulttimeout(60)
#########################CONTROL OBJECT DEFINITIONS#############################
pixels = np.zeros((512, 3), dtype='float32')
diff = np.zeros((512, 3), dtype='float32' )
endVals = np.zeros((512, 3), dtype='float32')
remaining = np.zeros((512), dtype='uint16')

clockerActive = threading.Event()

commands = queue.Queue(maxsize=100)
frameRate = 16
FCclient = opc.Client('localhost:7890')
arbitration = [False, '127.0.0.1']

##################SERVER LOGGING AND REPORTING FUNCTIONS########################
def logError(err):
    print(err)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'opcBridge-log.txt'), 'a') as logFile:
        logFile.write(err)
        logFile.write('\n')

bootMsg = 'Server booted at ' + str(datetime.datetime.now()) + '\n'
logError(bootMsg)
############################SUPPORT FUNCTIONS###################################
def pixelsToJson(npArray):
    lstOut = []
    for i in npArray:
        lstOut.append([int(i[0]), int(i[1]), int(i[2])])
    return lstOut

def makeEightBit(value):
    return min(255, max(0, int(value)))

def rgbSetBrightness(setBri, rgb):
    currentBri = max(rgb)
    ratio = setBri / currentBri
    rgbOut = [rgb[0] * ratio, rgb[1] * ratio, rgb[2] * ratio]
    return rgbOut

def brightnessChange(rgb, magnitude):
    '''Will take an RGB value and a brigtness change and spit out what its final value should be'''
    currentBri = max(rgb)
    if currentBri:
        newBri = currentBri + magnitude
        newBri = min(255, max(0, int(newBri)))
        if not newBri:
            newBri = 1
        if currentBri == newBri:
            return rgb
        rgbOut = rgbSetBrightness(newBri, rgb)
        return rgbOut
    else:
        return rgb

def bridgeValues(totalSteps, start, end):
    '''Generator that creates interpolated steps between a start and end value'''
    newRGB = start
    diffR = (end[0] - start[0]) / float(totalSteps)
    diffG = (end[1] - start[1]) / float(totalSteps)
    diffB = (end[2] - start[2]) / float(totalSteps)
    for i in range(totalSteps - 1):
        newRGB = [newRGB[0] + diffR, newRGB[1] + diffG, newRGB[2] + diffB]
        yield [int(newRGB[0]), int(newRGB[1]), int(newRGB[2])]
    yield end

def psuSwitch(state):
    ip = configs['PSUs']['ip']
    port = configs['PSUs']['port']
    state = json.dumps(state)
    params = {'index': configs['PSUs']['index'], 'state': state}
    requests.get('http://' + ip + ':' + str(port) + '/switch', params=params)

def psuCheck(pixels):
    for pix in pixels:
        for color in pix:
            if color > 0:
                return True
    return False

def runPSU():
    if not psuCheck(pixels):
        print('Spinning up PSU')
        psuSwitch(True)

#############################RENDER LOOP########################################

def clockLoop():
    '''Processes individual frames'''
    print('Initiating Clocker...')
    while 1:
        now = time.perf_counter()
        while not commands.empty():
            newCommand, args = commands.get()
            try:
                newCommand(*args)
            except Exception as e:
                print('YA FUCKED SOMETHING UP YOU IDIOT')
                logError(str(e))


        anyRemaining = False

        for pix in range(512):
            if not remaining[pix]:
                pass
            elif remaining[pix] > 1:
                for i in range(3):
                    pixels[pix][i] += diff[pix][i]
                remaining[pix] -= 1
                anyRemaining = True
            elif remaining[pix] == 1:
                pixels[pix] = endVals[pix]
                remaining[pix] -= 1
                anyRemaining = True

        try:
            FCclient.put_pixels(pixels)
        except Exception as e:
            print('FCserver is down')
        cycleTime = time.perf_counter() - now
        time.sleep(max((1 / frameRate) - cycleTime, 0))
        if not anyRemaining:
            if not psuCheck(pixels):
                print('Killing PSUs')
                psuSwitch(False)
            if commands.empty():
                clockerActive.clear()
                print('Sleeping clocker...')
        clockerActive.wait()
##################ARRAY MANIPULATING FUNCTIONS##################################
def absoluteFade(rgb, indexes, fadeTime):
    runPSU()
    if not fadeTime:
        fadeTime = 2 / frameRate
    frames = int(fadeTime * frameRate)
    for i in indexes:
        remaining[i] = frames
        for c in range(3):
            diff[i][c] = (rgb[c] - pixels[i][c]) / frames
        endVals[i] = rgb

def multiCommand(commandList):
    runPSU()
    for x in commandList:
        indexes = x[0]
        frames = int(x[2] * frameRate)
        if not frames:
            frames = 1
        rgb = x[1]
        for i in indexes:
            remaining[i] = frames
            for c in range(3):
                diff[i][c] = (rgb[c] - pixels[i][c]) / frames
            endVals[i] = rgb

def relativeFade(magnitude, indexes, fadeTime):
    runPSU()
    commandList = []
    for i in indexes:
        endVal = brightnessChange(pixels[i], magnitude)
        commandList.append([[i], endVal, fadeTime])
    multiCommand(commandList)

###################COMMAND TYPE HANDLING########################################
class Pixels(Resource):
    def get(self):
        '''Gives the entire pixel array back to the client as a 512 * 3 array'''
        print('\nSending pixels to %s \n' % request.remote_addr)
        message = pixelsToJson(pixels)
        return message
api.add_resource(Pixels, '/pixels')

class Arbitration(Resource):
    def put(self):
        args = parser.parse_args()
        id = args['id']
        ip = request.remote_addr
        print('\nGiving arbitration to %s from %s\n' % (id, ip))
        arbitration[0] = id
        arbitration[1] = ip

    def get(self):
        args = parser.parse_args()
        id = args['id']
        ip = request.remote_addr
        print('\nSending arbitration to %s for %s\n' % (ip, id))
        if id != arbitration[0]:
            return False
        elif ip != arbitration[1]:
            return False
        else:
            return True
api.add_resource(Arbitration, '/arbitration')

class AbsoluteFade(Resource):
    '''Is given a color to fade to, and executes fade'''
    def get(self):
        args = parser.parse_args()
        fadeTime = args['fadetime']
        rgb = args['rgb']
        indexes = args['indexes']
        commands.put((absoluteFade, [rgb, indexes, fadeTime]))
        clockerActive.set()
api.add_resource(AbsoluteFade, '/absolutefade')

class MultiCommand(Resource):
    def get(self):
        args = parser.parse_args()
        commandList = args['commandlist']
        commands.put((multiCommand, [commandList]))
        clockerActive.set()
api.add_resource(MultiCommand, '/multicommand')

class RelativeFade(Resource):
    '''Is given a brightness change, and alters the brightness, likely unpredicatable
    behavior if called in the middle of another fade'''
    def get(self):
        args = parser.parse_args()
        indexes = args['indexes']
        magnitude = args['magnitude']
        fadeTime = args['fadetime']
        commands.put((relativeFade, [magnitude, indexes, fadeTime]))
        clockerActive.set()
api.add_resource(RelativeFade, '/relativefade')

clocker = threading.Thread(target=clockLoop)

#Test pattern to indicate server is up and running
testPatternOff = np.zeros((512, 3))
testPatternRed = np.full((512, 3), [64,0,0])

FCclient.put_pixels(testPatternRed)
FCclient.put_pixels(testPatternRed)
time.sleep(.5)
FCclient.put_pixels(testPatternOff)
FCclient.put_pixels(testPatternOff)
time.sleep(.5)
FCclient.put_pixels(testPatternRed)
FCclient.put_pixels(testPatternRed)
time.sleep(.5)
FCclient.put_pixels(testPatternOff)
FCclient.put_pixels(testPatternOff)

del testPatternOff
del testPatternRed

#Initiate server
clocker.daemon = True
clocker.start()
fetcher.run(host=localIP, port=8000, debug=FLASK_DEBUG)
