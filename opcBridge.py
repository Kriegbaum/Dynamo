import opc
import time
import socket
import sys
import json
import threading
import queue

#typical command
#{'type': 'absoluteFade', 'index range': [0,512], 'color': [r,g,b], 'fade time': 8-bit integer}
#{'type': 'pixelRequest'}
#{'type': 'relativeFade', 'index range': [0,512] 'positive': True, 'magnitude': 8-bit integer, 'fade time': 8-bit integer}

#typical queue item
#[{index: [r,g,b], index2, [r,g,b]}, {index: [r,g,b], index2: [r,g,b]}]
##########################GET LOCAL IP##########################################
ipSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ipSock.connect(('8.8.8.8', 80))
localIP = ipSock.getsockname()[0]
ipSock.close()


#########################CONTROL OBJECT DEFINITIONS#############################
pixels = [ [255,0,0] ] * 512
commands = queue.Queue(maxsize=100)
queue = queue.Queue(maxsize=4500)
frameRate = 24
FCclient = opc.Client('localhost:7890')
queueLock = threading.Lock()
arbitration = False

############################SUPPORT FUNCTIONS###################################

def brightnessChange(rgb, magnitude, positive):
    '''INCOMPLETE: Will take an RGB value and a brigtness change and spit out what its final value should be'''
    majorColor = rgb.index(max(rgb))

    if positive:
        pass
    else:
        pass

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


#############################SERVER LOOPS#######################################


def queueLoop():
    '''Grabs new commands and populates the queue'''
    print('Initiating queuer')
    while True:
        if not commands.empty():
            print('Processing command...')
            newCommand = commands.get()
            commands.task_done()
            commandParse(newCommand)

def clockLoop():
    '''Removes items from the queue and transmits them to the controller'''
    print('Initiating Clocker')
    while True:
        if not queue.empty():
            now = time.time()
            alteration = queue.get()
            queue.task_done()
            for alt in alteration:
                pixels[alt] = alteration[alt]
            FCclient.put_pixels(pixels)
            while time.time() <= now + (1 / frameRate):
                pass

def fetchLoop():
    '''Fetches commands from the socket'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (localIP, 8000)
    print('Initiating socket on %s port %s' % server_address)
    sock.bind(server_address)
    sock.listen(5)
    while True:
        connection, client_address = sock.accept()
        print('Connection from', client_address)
        command = ''
        while True:
            data = connection.recv(16).decode()
            command += data
            if data:
                pass
            else:
                comDict = json.loads(command)
                commands.put(comDict)
                commands.task_done()
                break



###################COMMAND TYPE HANDLING########################################
def getArbitration():


def commandParse(command):
    if command['type'] == 'absoluteFade':
        absoluteFade(range(command['index range'][0], command['index range'][1]), command['color'], command['fade time'])
    elif command['type'] == relativeFade:
        pass
    elif command['type'] == pixelRequest:
        pass

def absoluteFade(indexes, rgb, fadeTime):
    '''Is given a color to fade to, and executes fade'''
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


def relativeFade(indexes, positive, magnitude, fadeTime):
    '''Is given a brightness change, and alters the brightness'''
    for i in indexes:
        start = pixels[i]
        if start == [0,0,0]:
            start = [1,1,1]
        endVal = brightnessChange(pixels[i], magnitude, positive)
        absoluteFade(range(i), endVal, fadeTime)


def pixelRequest():
    '''informs the server of current pixel values'''
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
