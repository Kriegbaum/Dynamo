#Located at github trevordavies095/DmxPy <- Python 3 port
import time
import os
import socket
import sys
import json
import threading
import queue
import datetime
import atexit

#Are we using the nice DMX box or not? The pro box doesnt need OLA, the openDMX box does
CHANNEL_CAP = 50
OLA = False
if OLA:
    import requests
    olaUrl = 'http://localhost:9090/set_dmx'
else:
    from DmxPy import DmxPy
    #TODO: find a way to locate DMX interface amongst other USB devices
    dmx = DmxPy('/dev/ttyUSB0')

#This will log EVERYTHING, disable when you've ceased being confused about your socket issues
#sys.stdout = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dmxBridge-log.txt'), 'w')

#typical command
#{'type': 'absoluteFade', 'targetValues', [[address 1, value 1], [address 2, value 2]], 'fadeTime': 8-bit integer}
#{'type': 'pixelRequest'}
#{'type': 'relativeFade', 'index range': [0,512] 'positive': True, 'magnitude': 8-bit integer, 'fadeTime': 8-bit integer}
#('type': 'multiCommand', [[targetValues 1, fadeTime1], [targetValues 2, fadeTime2]])

#typical queue item
#[{index: [r,g,b], index2, [r,g,b]}, {index: [r,g,b], index2: [r,g,b]}]
##########################GET LOCAL IP##########################################
ipSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    ipSock.connect(('10.255.255.255', 1))
    localIP = ipSock.getsockname()[0]
except:
    localIP = '127.0.0.1'
ipSock.close()

socket.setdefaulttimeout(60)
#########################CONTROL OBJECT DEFINITIONS#############################
commands = queue.Queue(maxsize=100)
queue = queue.Queue(maxsize=4500)
frameRate = 44
pixels = [0] * CHANNEL_CAP
#TODO: Figure out how to detect which serial port the EntTech driver is on)
queueLock = threading.Lock()
arbitration = [False]

############################SUPPORT FUNCTIONS###################################
def clampEightBit(value):
    return min(255, max(0, int(value)))

def sixteenToEight(value):
    high = (value & 0xFF00) // 256
    low = value & 0x00FF
    return [high, low]

def brightnessChange(rgb, magnitude, positive):
    '''INCOMPLETE: Will take an RGB value and a brigtness change and spit out what its final value should be'''
    majorColor = rgb.index(max(rgb))

    rgbOut = [rgb[0] + magnitude, rgb[1] + magnitude, rgb[2] + magnitude]

    if positive:
        if max(rgbOut) > 255:
            decrease = max(rgbOut) - 255
            for value in rgbOut:
                value -= decrease

    else:
        if min(rgbOut) < 0:
            increase = abs(min(rgbOut))
            for value in rgbOut:
                value += increase

    return rgbOut

def bridgeValues(totalSteps, start, end):
    '''Generator that creates interpolated steps between a start and end value'''
    new = start
    diff = (end - start) / float(totalSteps)
    for i in range(totalSteps - 1):
        new = new + diff
        yield new
    yield end

def socketKill(sock):
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
#############################SERVER LOOPS#######################################


def queueLoop():
    '''Grabs new commands and populates the queue'''
    print('Initiating queuer')
    while True:
        newCommand = commands.get(True, None)
        commands.task_done()
        commandParse(newCommand)

def clockLoop():
    '''Removes items from the queue and transmits them to the controller'''
    print('Initiating Clocker')
    while True:
        #This was one line further down, probably a mistake
        alteration = queue.get(True, None)
        queueLock.acquire()
        queue.task_done()
        for alt in alteration:
            pixels[alt] = alteration[alt]
        if OLA:
            listStr = str(pixels)[1:-1]
            requests.post(olaUrl, data={'u':1, 'd':listStr})
        else:
            for alt in alteration:
                dmx.setChannel(alt, alteration[alt])
            dmx.render()
        queueLock.release()
        time.sleep((1 / frameRate) * .75)

def fetchLoop():
    '''Fetches commands from the socket'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #server_address = (localIP, 8000)
    server_address = (localIP, 8002)
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
                commands.put(comDict)
                break

###################COMMAND TYPE HANDLING########################################

def commandParse(command):
    if command['type'] == 'absoluteFade':
        absoluteFade(command['targetValues'], command['fadeTime'], False)
    elif command['type'] == 'absolute16bit':
        absoluteFade(command['targetValues'], command['fadeTime'], True)
    elif command['type'] == 'relativeFade':
        pass
    elif command['type'] == 'pixelRequest':
        pass
    elif command['type'] == 'requestArbitration':
        getArbitration(command['ip'])
    elif command['type'] == 'setArbitration':
        setArbitration(command['setting'])
    elif command['type'] == 'multiCommand':
        multiCommand(command['commands'])
    else:
        print('Invalid command type recieved')
        print(command['type'] + 'is not a valid command')

def setArbitration(setting):
    if type(setting) != bool:
        print('Invalid arbitration setting, must be bool')
    else:
        arbitration[0] = setting

def getArbitration(ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip, 8802)
    sock.connect(server_address)
    message = json.dumps(arbitration[0])
    try:
        sock.sendall(message.encode())
    except Exception as e:
        print('Failed returning arbitration, ' + e)
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

def absoluteFade(targetValues, fadeTime, sixteenBit):
    '''Is given a dictionary of indexes and their targetValues, and a fadeTime'''
    print('Fading now')
    targetValues = {int(k): int(v) for k, v in targetValues.items()}
    if not fadeTime:
        fadeTime = 1 / frameRate
    print(targetValues)
    #Calculates how many individual fade frames are needed
    alterations = int(fadeTime * frameRate)
    queueList = []
    queueLock.acquire()
    while not queue.empty():
        queueList.append(queue.get())
        queue.task_done()
    #Amount of frames that need to be added to queue
    appends = alterations - len(queueList)
    #fill out the queue with blank dictionaries to populate
    if appends > 0:
        for i in range(abs(appends)):
            queueList.append({})
    #Iterate down indexes, figure out what items in queue need to be altered
    for i in targetValues:
        #INVESTIGATE: THIS MIGHT BE THE SOURCE OF FLASHING ISSUES AT THE START OF A COMMAND
        start = pixels[i]
        end = targetValues[i]
        bridgeGenerator = bridgeValues(alterations, start, end)
        print('Index %d' % i)
        print('Start fade at %d' % start)
        print('End fade at %d' % end)
        for m in range(alterations):
            if sixteenBit:
                value = int(next(bridgeGenerator))
                highLow = sixteenToEight(value)
                queueList[m][i] = highLow[0]
                queueList[m][i + 1] = highLow[1]
            else:
                queueList[m][i] = int(next(bridgeGenerator))
    #If this command overrides a previous command to the pixel, it should wipe any commands remaining
        if appends < 0:
            for r in range(abs(appends)):
                if i in queueList[alterations + r]:
                    del queueList[alterations + r][i]
                    if sixteenBit:
                        del queueList[alterations + r][i + 1]
    while queueList:
        queue.put(queueList.pop(0))
    queueLock.release()

def multiCommand(commands):
    maxAlterations = int(max([i[2] for i in commands]) * frameRate)
    queueList = []
    queueLock.acquire()
    while not queue.empty():
        queueList.append(queue.get())
        queue.task_done()
    appends = maxAlterations - len(queueList)
    if appends > 0:
        for i in range(abs(appends)):
            queueList.append({})
    for c in commands:
        commandAlterations = int(c[2] * frameRate)
        for i in range(c[0][0], c[0][1]):
            start = pixels[i]
            bridgeGenerator = bridgeValues(commandAlterations, start, c[1])
            for m in range(commandAlterations):
                queueList[m][i] = next(bridgeGenerator)
        if appends < 0:
            for r in range(abs(appends)):
                if i in queueList[commandAlterations + r]:
                    del queueList[commandAlterations + r][i]
    while queueList:
        queue.put(queueList.pop(0))
    queueLock.release()



def relativeFade(indexes, positive, magnitude, fadeTime):
    '''Is given a brightness change, and alters the brightness'''
    for i in indexes:
        start = pixels[i]
        if start == [0,0,0]:
            start = [1,1,1]
        endVal = brightnessChange(pixels[i], magnitude, positive)
        absoluteFade(range(i), endVal, fadeTime)


def pixelRequest():
    '''informs the client of current pixel values'''
    return pixels

clocker = threading.Thread(target=clockLoop)
fetcher = threading.Thread(target=fetchLoop)
queuer =  threading.Thread(target=queueLoop)


#Initiate server
fetcher.start()
queuer.start()
clocker.start()
