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


command1 = {'type': 'absoluteFade', 'color': [255,255,255], 'fade time': 1, 'index range': [0,150]}
command2 = {'type': 'absoluteFade', 'color': [0,0,0], 'fade time': 10, 'index range': [0,150]}

sendCommand(command1)
time.sleep(1)
sendCommand(command2)
