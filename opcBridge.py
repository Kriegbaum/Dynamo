import opc
import time
import socket
import sys
import json
import threading

#sample command
#{'type': 'absoluteFade', 'index range': [0,512], 'color': [r,g,b], 'fade time': 8-bit integer}
#{'type': 'pixelRequest'}
#{'type': 'relativeFade', 'index range': [0,512] 'positive': True, 'magnitude': 8-bit integer, 'fade time': 8-bit integer}

#sample queue item
#[{index: [r,g,b], index2, [r,g,b]}, {index: [r,g,b], index2: [r,g,b]}]


#########################CONTROL OBJECT DEFINITIONS#############################
pixels = [ [0,0,0] ] * 512
commands = []
queue = []
frameRate = 24
FCclient = opc.Client('localhost:7890')
pixelLock = False
commandLock = False
queueLock = False

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
        commandLock = True
        if commands:
            if not queueLock:
                pixelLock = True
                print('Oh, uh, hey')
                print('I got a thing')
                newCommand = commands.pop(0)
                commandParse(newCommand)
                pixelLock = False
                command = newCommand
        commandLock = False

def clockLoop():
    '''Removes items from the queue and transmits them to the controller'''
    print('Initiating Clocker')
    while True:
        if not pixelLock:
            queueLock = True
            if queue:
                alteration = queue.pop(0)
                print(pixels[0])
                queueLock = False
                pixelLock = True, client_address
                for q in alteration:
                    pixels[q] = alteration[q]
                FCclient.put_pixels(pixels)
                pixelLock = False
            else:
                queueLock = False
        time.sleep(1/frameRate)

def fetchLoop():
    '''Fetches commands from the socket'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 8000)
    print('Initiating socket on %s port %s' % server_address)
    sock.bind(server_address)

    sock.listen(1)
    print('I\'m, uh, LISTENING!')
    while True:
        connection, client_address = sock.accept()


        print('Hey, I found a guy, he is', client_address)
        command = ''
        while True:
            data = connection.recv(16).decode()
            command += data
            if data:
                pass
            else:
                print('Hey, that guy SUCKS')
                break
        comDict = json.loads(command)
        """while commandLock:
            pass
        commandLock = True"""
        commands.append(comDict)
        #commandLock = False


###################COMMAND TYPE HANDLING########################################
def commandParse(command):
    print('starting commandParse')
    if command['type'] == 'absoluteFade':
        absoluteFade(range(command['index range'][0], command['index range'][1]), command['color'], command['fade time'])
    elif command['type'] == relativeFade:
        pass
    elif command['type'] == pixelRequest:
        pass

def absoluteFade(indexes, rgb, fadeTime):
    '''Is given a color to fade to, and executes fade'''
    print('Starting absoluteFade')
    #Calculates how many individual fade frames are needed
    alterations = int(fadeTime * frameRate)
    #Amount of frames that need to be added to queue
    appends = alterations - len(queue)
    if appends < 0:
        appends = 0
    #fill out the queue with blank dictionaries to populate
    if appends > 0:
        for i in range(appends):
            queue.append({})
    #Iterate down indexes, figure out what items in queue need to be altered
    for i in indexes:
        start = pixels[i]
        bridgeGenerator = bridgeValues(alterations, start, rgb)
        for m in range(alterations):
            queue[m][i] = next(bridgeGenerator)


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


fetcher.start()
queuer.start()
#clocker.start()
