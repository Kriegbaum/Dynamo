import socket
import sys
import json
import time

def sendCommand(command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = ('192.168.1.244', 8000)
    print('connecting to %s port %s' % server_address)
    sock.connect(server_address)


    message = json.dumps(command)
    try:
        print('sending %s' % message)
        sock.sendall(message.encode())

    finally:
        print('Closing socket 1')
        sock.close()


command1 = {'type': 'absoluteFade', 'color': [255,255,255], 'fade time': 10, 'index range': [0,15]}
command2 = {'type': 'absoluteFade', 'color': [0,0,255], 'fade time': 20, 'index range': [15,30]}
command3 = {'type': 'absoluteFade', 'color': [255,0,0], 'fade time': 30, 'index range': [30,60]}
command4 = {'type': 'absoluteFade', 'color': [255,255,255], 'fade time': 40, 'index range': [65,128]}

sendCommand(command1)

sendCommand(command2)

sendCommand(command3)

sendCommand(command4)
