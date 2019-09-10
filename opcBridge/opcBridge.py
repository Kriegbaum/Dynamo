import opc
import time
import os
import socket
import sys
import json
import threading
import queue
import datetime
import atexit
import numpy as np

#This will log EVERYTHING, disable when you've ceased being confused about your socket issues
#sys.stdout = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'opcBridge-log.txt'), 'w')

#typical command
#{'type': 'absoluteFade', 'indexRange': [0,512], 'color': [r,g,b], 'fadeTime': 8-bit integer}
#{'type': 'pixelRequest'}
#{'type': 'relativeFade', 'indexRange': [0,512] 'positive': True, 'magnitude': 8-bit integer, 'fadeTime': 8-bit integer}
#('type': 'multiCommand', [[fixture1, rgb1, fadeTime1], [fixture2, rgb2, fadeTime2]])

#typical queue item
#[{index: [r,g,b], index2, [r,g,b]}, {index: [r,g,b], index2: [r,g,b]}]
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
pixels = np.zeros((512, 3))
diff = np.zeros((512, 3))
endVals = np.zeros((512, 3), dtype='uint8')
remaining = np.zeros((512), dtype='uint16')

clockLock = threading.Lock()
clockerActive = threading.Event()

commands = queue.Queue(maxsize=100)
frameRate = 15
FCclient = opc.Client('localhost:7890')
queueLock = threading.Lock()
arbitration = [False, '127.0.0.1']

##################SERVER LOGGING AND REPORTING FUNCTIONS########################
def constructErrorEntry(ip, err):
    stringOut = str(datetime.datetime.now())
    stringOut += ' from %s ' % ip
    stringOut += str(err)
    return stringOut

def returnError(ip, err):
    '''Send a report of an error back to the device that caused it'''
    errSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        errSock.connect((ip, 8880))
        errSock.sendall(err.encode())
    except Exception as e:
        print(e)
    finally:
        errSock.shutdown(socket.SHUT_RDWR)
        errSock.close()

def logError(err):
    with open(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'opcBridge-log.txt'), 'a') as logFile:
        logFile.write(err)

def ripServer(ip, err):
    err = constructErrorEntry(ip, err)
    logError(err)
    returnError(ip, err)

############################SUPPORT FUNCTIONS###################################
def pixelsToJson(npArray):
    lstOut = []
    for i in npArray:
        lstOut.append(list(i))
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
        rgbOut = rgbSetBrightness(newBri, rgb)
    else:
        rgbOut = rgb
    return rgbOut

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

def socketKill(sock):
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
#############################SERVER LOOPS#######################################


def queueLoop():
    '''Grabs commands from queue and modifies clock arrays'''
    print('Initiating queuer')
    while True:
        newCommand = commands.get(True, None)
        commands.task_done()
        try:
            commandParse(newCommand)
        except:
            print('YA FUCKED SOMETHING UP YOU IDIOT')

def clockLoop():
    '''Processes individual frames'''
    print('Initiating Clocker...')
    now = time.perf_counter()
    while True:
        anyRemaining = False
        now = time.perf_counter()

        clockLock.acquire()
 #       print('Clocklock acquired in clockLoop')
        for pix in range(512):
            if remaining[pix] > 1:
                for i in range(3):
                    pixels[pix][i] += diff[pix][i]
                remaining[pix] -= 1
                anyRemaining = True
            elif remaining[pix] == 1:
                pixels[pix] = endVals[pix]
                remaining[pix] -= 1
                anyRemaining = True
        clockLock.release()
#        print('Clocklock released in clockLoop')

        try:
            FCclient.put_pixels(pixels)
        except Exception as e:
            print('FCserver is down')
        cycleTime = time.perf_counter() - now
        sleepTime = max((1 / frameRate) - cycleTime, 0)
        if not sleepTime:
            print('PERFORMANCE HIT')
        time.sleep(sleepTime)
        if not anyRemaining:
            clockerActive.clear()
            print('Sleeping clocker...')
        clockerActive.wait()

def fetchLoop():
    '''Fetches commands from the socket'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (localIP, 8000)
    print('Initiating socket on %s port %s' % server_address)
    sock.bind(server_address)
    sock.listen(90)
    sock.settimeout(None)
    atexit.register(socketKill, sock)
    while True:
        connection, client_address = sock.accept()
        command = ''
        while True:
            data = connection.recv(16).decode()
            command += data
            if data:
                pass
            else:
                comDict = json.loads(command)
                print(datetime.datetime.now(), comDict['type'] + ' recieved from', client_address)
                comDict['ip'] = client_address[0]
                commands.put(comDict)
                break

###################COMMAND TYPE HANDLING########################################

def commandParse(command):
    if command['type'] == 'absoluteFade':
        try:
            if 'indexRange' in command:
                absoluteFade(range(command['indexRange'][0], command['indexRange'][1]), command['color'], command['fadeTime'])
            else:
                absoluteFade(command['indexes'], command['color'], command['fadeTime'])
        except Exception as err:
            ripServer(command['ip'], err)
    elif command['type'] == 'relativeFade':
        try:
            relativeFade(command['indexRange'], command['magnitude'], command['fadeTime'])
        except Exception as err:
            ripServer(command['ip'], err)
    elif command['type'] == 'getPixels':
        try:
            getPixels(command['ip'])
        except Exception as err:
            ripServer(command['ip'], err)
    elif command['type'] == 'getArbitration':
        try:
            getArbitration(command['id'], command['ip'])
        except Exception as err:
            ripServer(command['ip'], err)
    elif command['type'] == 'setArbitration':
        try:
            setArbitration(command['id'], command['ip'])
        except Exception as err:
            ripServer(command['ip'], err)
    elif command['type'] == 'multiCommand':
        try:
            multiCommand(command['commands'])
        except Exception as err:
            ripServer(command['ip'], err)
    else:
        err = 'Invalid command type recieved' + command['type'] + 'is not a valid command'
        ripServer(command['ip'], err)

def getPixels(ip):
    '''Gives the entire pixel array back to the client as a 512 * 3 array'''
    print('\nSending pixels to %s \n' % ip)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip, 8800)

    clockLock.acquire()
#    print('ClockLock acquired in getPixels')
    message = json.dumps(pixelsToJson(pixels))
    clockLock.release()
#    print('Clocklock released in getPixels')

    try:
        sock.connect(server_address)
        sock.sendall(message.encode())
        sock.shutdown(socket.SHUT_RDWR)
    except Exception as err:
        print(err)
    finally:
        sock.close()

def setArbitration(id, ip):
    print('\nGiving arbitration to %s from %s\n' % (id, ip))
    arbitration[0] = id
    arbitration[1] = ip

def getArbitration(id, ip):
    print('\nSending arbitration to %s for %s\n' % (ip, id))
    try:
        if id != arbitration[0]:
            response = False
        elif ip != arbitration[1]:
            response = False
        else:
            response = True
    except Exception as err:
        ripServer(ip, err)
        response = False

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip, 8800)
    sock.connect(server_address)
    message = json.dumps(response)
    try:
        sock.sendall(message.encode())
    except Exception as err:
        ripServer(ip, err)
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

def absoluteFade(indexes, rgb, fadeTime):
    '''Is given a color to fade to, and executes fade'''
    print('\nInitiating Fade to %s\n' % rgb)
    if not fadeTime:
        fadeTime = 2 / frameRate
    frames = int(fadeTime * frameRate)
    clockLock.acquire()
    print('Clocklock aquired in absolutefade')
    for i in indexes:
        remaining[i] = frames
        for c in range(3):
            diff[i][c] = (rgb[c] - pixels[i][c]) / frames
        endVals[i] = rgb
    clockLock.release()
    print('clocklock released in absolutefade')
    clockerActive.set()
#    print('clockeractive set in absolutefade')


def multiCommand(commands):
    for c in commands:
        indexes = range(c[0][0], c[0][1])
        rgb = c[1]
        fadeTime = c[2]
        absoluteFade(indexes, rgb, fadeTime)

def relativeFade(indexes, magnitude, fadeTime):
    '''Is given a brightness change, and alters the brightness, likely unpredicatable
    behavior if called in the middle of another fade'''
    commandList = []
    clockLock.acquire()
    print(indexes, magnitude, fadeTime)
    print('Clocklock acquired in relativeFade')
    try:
        for i in range(indexes[0], indexes[1]):
            endVal = brightnessChange(pixels[i], magnitude)
            print('cleared brightness change')
            commandList.append([[i, i + 1], endVal, fadeTime])
    except Exception as e:
         print(e)
    clockLock.release()
    print('Clocklock released in relativeFade')
    multiCommand(commandList)

clocker = threading.Thread(target=clockLoop)
fetcher = threading.Thread(target=fetchLoop)
queuer =  threading.Thread(target=queueLoop)


#Test pattern to indicate server is up and running
testPatternOff = np.zeros((512, 3))
testPatternRed = np.full((512, 3), [255,0,0])

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
fetcher.start()
queuer.start()
clocker.start()
