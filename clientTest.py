import socket
import sys
import json
import time

def sendCommand(command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = ('localhost', 8000)
    print('connecting to %s port %s' % server_address)
    sock.connect(server_address)


    message = json.dumps(command)
    try:
        print('sending %s' % message)
        sock.sendall(message.encode())

    finally:
        print('Closing socket 1')
        sock.close()


for i in range(50):
    command = {'type': 'absoluteFade', 'color': [255,0,0], 'fade time': (50/2) - (i/2), 'index range': [i,i + 1]}
    sendCommand(command)
    time.sleep((25 / 48) - (i / 96))
