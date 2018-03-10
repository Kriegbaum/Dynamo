import opc
import time
import socket
import sys
import json

#sample command
#{'type': 'absoluteFade', 'index range': [0,512], 'color': [r,g,b], 'fade time': 8-bit integer}
#{'type': 'pixelRequest'}
#{'type': 'relativeFade', 'index range': [0,512] 'positive': True, 'magnitude': 8-bit integer, 'fade time': 8-bit integer}

#sample queue item
#[{index: [r,g,b], index2, [r,g,b]}, {index: [r,g,b], index2: [r,g,b]}]


#########################CONTROL OBJECT DEFINITIONS#############################
pixels = [ [0,255,128] ] * 512
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

def bridgeValues(totalSteps, start, end):
    '''Generator that creates interpolated steps between a start and end value'''
    newRGB = start
    diffR = (end[0] - start[0]) / float(totalSteps)
    diffG = (end[1] - start[1]) / float(totalSteps)
    diffB = (end[2] - start[2]) / float(totalSteps)
    for i in range(totalSteps):
        newRGB = [newRGB[0] + diffR, newRGB[1] + diffG, newRGB[2] + diffB]
        yield newRGB
    yield end


#############################SERVER LOOPS#######################################


def queueLoop():
    '''Grabs new commands and populates the queue'''
    while True:
        commandLock = True
        if commands:
            if not queueLock:
                pixelLock = True
                commandParse(newCommand, queue)
                pixelLock = False
                command = newCommand
        commandLock = False

def clockLoop():
    '''Removes items from the queue and transmits them to the controller'''
    while True:
        if not pixelLock:
            queueLock = True
            alteration = queue.pop(0)
            queueLock = False
            for q in alteration:
                pixels[q] = alteration[q]
            print(pixels[0])
            FCclient.put_pixels(pixels)
        time.sleep(1/frameRate)

def fetchLoop():
    '''Fetches commands from the socket'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 8000)
    print('Initiating socket on %s port %s' % server_address)
    sock.bind(server_address)

    sock.listen(1)
    while True:
        print('I\'m, uh, LISTENING!')
        connection, client_address = sock.accept()

        try:
            print('Hey, I found a guy, he is', client_address)
            command = ''
            while True:
                data = connection.recv(16).decode()
                command += data
                if data:
                    pass
                else:
                    print('Hey, that guy SUCKS', client_address)
                    print('Oh, by the way, he says', command)
                    break
            comDict = json.loads(command)
            commands.append(comDict)
        except:
            pass

###################COMMAND TYPE HANDLING########################################

def absoluteFade(indexes, rgb, fadeTime):
    '''Is given a color to fade to, and executes fade'''
    #Calculates how many individual fade frames are needed
    alterations = fadeTime * frameRate
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
    '''INCOMPLETE: Is given a brightness change, and alters the brightness'''
    for i in indexes:
        pass


def pixelRequest():
    '''informs the server of current pixel values'''
    return pixels


absoluteFade(range(100), [0,128,255], 6)
clockLoop()
