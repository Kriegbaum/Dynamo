import socket
import sys
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('localhost', 10000)
print('connecting to %s port %s' % server_address)
sock.connect(server_address)

try:
    command = {'brightness':100, 'hue':360, 'saturation': 255, 'name': 'Jimberylflubbs'}
    message = json.dumps(command)
    print('sending %s' % message)
    sock.sendall(message.encode())

finally:
    print('closing socket')
    sock.close()
