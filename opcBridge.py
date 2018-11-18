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

#This will log EVERYTHING, disable when you've ceased being confused about your socket issues
sys.stdout = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'opcBridge-log.txt'), 'w')

#typical command
#{'type': 'absoluteFade', 'index range': [0,512], 'color': [r,g,b], 'fade time': 8-bit integer}
#{'type': 'pixelRequest'}
#{'type': 'relativeFade', 'index range': [0,512] 'positive': True, 'magnitude': 8-bit integer, 'fade time': 8-bit integer}
#('type': 'multiCommand', [[fixture1, rgb1, fadeTime1], [fixture2, rgb2, fadeTime2]])

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
pixels = [ [255,0,0] ] * 512
commands = queue.Queue(maxsize=100)
queue = queue.Queue(maxsize=4500)
frameRate = 20
FCclient = opc.Client('localhost:7890')
queueLock = threading.Lock()
arbitration = [False]

############################SUPPORT FUNCTIONS###################################
def makeEightBit(value):
    return min(255, max(0, int(value)))

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
        alteration = queue.get(True, None)
        queueLock.acquire()
        queue.task_done()
        for alt in alteration:
            pixels[alt] = alteration[alt]
        FCclient.put_pixels(pixels)
        time.sleep(1 / frameRate)
        queueLock.release()

def fetchLoop():
    '''Fetches commands from the socket'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #server_address = (localIP, 8000)
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
                commands.put(comDict)
                break

###################COMMAND TYPE HANDLING########################################

def commandParse(command):
    if command['type'] == 'absoluteFade':
        absoluteFade(range(command['index range'][0], command['index range'][1]), command['color'], command['fade time'])
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
    server_address = (ip, 8800)
    sock.connect(server_address)
    message = json.dumps(arbitration[0])
    try:
        sock.sendall(message.encode())
    except Exception as e:
        print('Failed returning arbitration, ' + e)
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

def absoluteFade(indexes, rgb, fadeTime):
    '''Is given a color to fade to, and executes fade'''
    if not fadeTime:
        fadeTime = 1 / frameRate
    for c in rgb:
        c = makeEightBit(c)
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
    for i in indexes:
        #INVESTIGATE: THIS MIGHT BE THE SOURCE OF FLASHING ISSUES AT THE START OF A COMMAND
        start = pixels[i]
        bridgeGenerator = bridgeValues(alterations, start, rgb)
        for m in range(alterations):
            queueList[m][i] = next(bridgeGenerator)
    #If this command overrides a previous command to the pixel, it should wipe any commands remaining
        if appends < 0:
            for r in range(abs(appends)):
                if i in queueList[alterations + r]:
                    del queueList[alterations + r][i]
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


#Test pattern to indicate server is up and running
FCclient.put_pixels(pixels)
time.sleep(1)
pixels = [ [0,0,0] ] * 512
FCclient.put_pixels(pixels)
time.sleep(1)
pixels = [ [255,0,0] ] * 512
FCclient.put_pixels(pixels)
time.sleep(1)
pixels = [ [0,0,0] ] * 512
FCclient.put_pixels(pixels)

#Initiate server
fetcher.start()
queuer.start()
clocker.start()
