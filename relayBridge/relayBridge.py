import socket
import json
import datetime
import atexit
from gpiozero import OutputDevice as Relay
import yaml
import queue
import threading
import os
import sys

#######################GET LOCAL IP####################################
ipSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    ipSock.connect(('10.255.255.255', 1))
    localIP = ipSock.getsockname()[0]
except Exception as e:
    print(e)
    print('Local IP detection failed, listening on localhost')
    localIP = '127.0.0.1'
ipSock.close()
socket.setdefaulttimeout(60)

def socketKill(sock):
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()

#########################CONTROL OBJECTS##############################
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'relayPatch.yml')) as f:
    relayPatch = f.read()
relayPatch = yaml.safe_load(relayPatch)
for relay in relayPatch:
    relayPatch[relay] = Relay(relayPatch[relay])
    #If this is not here, the server will immediately turn off everythin
    relayPatch[relay].on()
commands = queue.Queue(maxsize=100)
arbitration = [False, '121.0.0.1']


#####################SERVER LOGGING AND REPORTING#####################
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
###############################MAIN SERVER ACTIONS######################
def fetchLoop():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (localIP, 8001)
    print('Initating socket on %s port %s' % server_address)
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
                print(datetime.datetime.now(), comDict['type'], 'recieved from', client_address)
                comDict['ip'] = client_address[0]
                commands.put(comDict)
                break

def switchLoop():
    while True:
        switchCommand = commands.get(True, None)
        commands.task_done()
        commandParse(switchCommand)

def getState(ip, index):
    '''Gives the state of specified relay back to the client as a bool'''
    print('\nSending pixels to %s \n' % ip)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip, 8801)
    state = bool(relayPatch[index].value)
    message = json.dumps(state)
    try:
        sock.connect(server_address)
        sock.sendall(message.encode())
    except Exception as err:
        ripServer(ip, err)
    finally:
        sock.shutdown(socket.SHUT_RDWR)
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
    server_address = (ip, 8801)
    sock.connect(server_address)
    message = json.dumps(response)
    try:
        sock.sendall(message.encode())
    except Exception as err:
        ripServer(ip, err)
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

################################COMMAND TYPE HANDLING###########################
def commandParse(command):
    if command['type'] == 'switch':
        index = command['index']
        if command['state']:
            relayPatch[index].on()
        else:
            relayPatch[index].off()
    elif command['type'] == 'toggle':
        index = command['index']
        relayPatch[index].toggle()
    elif command['type'] == 'getState':
        index = command['index']
        getState(command['ip'], command['index'])
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
    else:
        print('Invalid command')
        ripServer(command['ip'], 'Invalid Command Type')

fetcher = threading.Thread(target=fetchLoop)
switcher = threading.Thread(target=switchLoop)

fetcher.start()
switcher.start()
