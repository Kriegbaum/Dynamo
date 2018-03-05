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
#[[index, [r,g,b]]], [index2, [r,g,b]]


#########################CONTROL OBJECT DEFINITIONS#############################
pixels = [[0,0,0] * 512]
commands = []
queue = []
frameRate = 20
FCclient = opc.Client('localhost:7890')
pixelLock = False
commandLock = False
queueLock = False

############################SUPPORT FUNCTIONS###################################

def brightnessChange(rgb, magnitude, positive):
'''INCOMPLETE: Will take an RGB value and a brigtness change and spit out what its final value should be'''
    majorColor = rgb.index(max(rgb))
    if positive:

def bridgeValues(totalSteps, start, end):
'''Generator that creates interpolated steps between a start and end value'''


#############################SERVER LOOPS#######################################


def queueLoop():
'''Grabs new commands and populates the queue'''
    while True:
        commandLock = True
        if commands:
            if !(queueLock):
                pixelLock = True
                commandParse(newCommand, queue)
                pixelLock = False
                command = newCommand
        commandLock = False

def clockLoop():
'''Removes items from the queue and transmits them to the controller'''
    while True:
        if !(pixelLock):
            queueLock = True
            alteration = queue.pop()
            queueLock = False
            for q in alteration:
                pixels[q[0]] = q[1]
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
            commands.append(command)

###################COMMAND TYPE HANDLING########################################


def absoluteFade(indexes, rgb, fadeTime):
'''Is given a color to fade to, and executes fade'''
    fadeTime * frameRate = alterations
    remaining = alterations
    alterations - len(queue) = qMod
    for i in indexes:
        stepsR = bridgeValues(alterations, pixels[i][0], rgb[0])
        stepsG = bridgeValues(alterations, pixels[i][1], rgb[1])
        stepsB = bridgeValues(alterations, pixels[i][2], rgb[2])
        for m in range(0,qMod):
            #BAD, FOR SHAME YOU THIS SUCKS NOT EVEN DEBUGGING READY
            #queue[m] = [i, [next(stepsR), next(stepsG), next(stepsB)]]
            remaining -= 1
        for a in range(remaining):
            #NOT GOOD, THIS DOES NOT GO ANY FURTHER THAN HERE
            #queue.append([i, [next(stepsR), next(stepsG), next(stepsB)]])

def relativeFade(indexes, positive, magnitude, fadeTime):
'''Is given a brightness change, and alters the brightness'''
    fadeTime * frameRate = alterations
    alterations - len(queue) = qMod
    for i in indexes:
        for m in range(0,qMod):
            queue[m]


def pixelRequest():
'''informs the server of current pixel values'''
    return pixels
