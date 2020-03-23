import socket
import datetime
from gpiozero import OutputDevice as Relay
import yaml
import queue
import threading
import os
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
import json

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

#########################CONTROL OBJECTS##############################
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'relayPatch.yml')) as f:
    relayPatch = f.read()
relayPatch = yaml.safe_load(relayPatch)
for relay in relayPatch:
    relayPatch[relay] = Relay(relayPatch[relay])
    #If this is not here, the server will immediately turn off everything
    relayPatch[relay].on()
commands = queue.Queue(maxsize=100)
arbitration = [False, '121.0.0.1']


#####################SERVER LOGGING AND REPORTING#####################
def logError(err):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'relayBridge-log.txt'), 'a') as logFile:
        logFile.write(err)

bootMsg = 'Server booted at ' + str(datetime.datetime.now()) + '\n'
logError(bootMsg)

############################FLASK APP###########################################
FLASK_DEBUG = True
fetcher = Flask(__name__)
api = Api(fetcher)
parser = reqparse.RequestParser()

#############################COMMAND FIELDS#####################################
parser.add_argument('index', type=int, help='Which relay is the command addressed to')
parser.add_argument('state', type=json.loads, help='True for on, false for off')
parser.add_argument('id', type=str, help='Arbitration id for server')

###############################MAIN SERVER ACTIONS######################
def switchLoop():
    while True:
        switchCommand, args = commands.get(True, None)
        try:
            switchCommand(*args)
        except Exception as e:
            print('Something went wrong, how could you do this?')
            logError(str(e))
        commandParse(switchCommand)

class State(Resource):
    '''Gives the state of specified relay back to the client as a bool'''
    def get(self):
        args = parser.parse_args()
        index = args['index']
        state = bool(relayPatch[index].value)
        return state
api.add_resource(State, '/state')

class Switch(Resource):
    '''Switches specified relay on or off'''
    def get(self):
        args = parser.parse_args()
        index = args['index']
        state = args['state']
        if state:
            relayPatch[index].on()
        else:
            relayPatch[index].off()
api.add_resource(Switch, '/switch')

class Toggle(Resource):
    def get(self):
        args = parser.parse_args()
        index = args['index']
        relayPatch[index].toggle()
        return bool(relayPatch[index].value)
api.add_resource(Toggle, '/toggle')

class Arbitration(Resource):
    '''Who has control over this server?'''
    def get(self):
        args = parser.parse_args()
        id = args['id']
        ip = request.remote_addr
        if id != arbitration[0]:
            return False
        elif ip != arbitration[1]:
            return False
        else:
            return True

    def put(self):
        args = parser.parse_args()
        id = args['id']
        ip = request.remote_addr
        arbitration[0] = id
        arbitration[1] = ip
api.add_resource(Arbitration, '/arbitration')

################################COMMAND TYPE HANDLING###########################
switcher = threading.Thread(target=switchLoop)
switcher.start()
fetcher.run(host=localIP, port=8001 debug=FLASK_DEBUG)
