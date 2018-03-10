import socket
import sys
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('localhost', 8000)
print('connecting to %s port %s' % server_address)
sock.connect(server_address)

try:
    command = {'type': 'absoluteFade', 'color': [255,255,255], 'fade time': 15, 'index range': [0,150]}
    message = json.dumps(command)
    print('sending %s' % message)
    sock.sendall(message.encode())

finally:
    print('closing socket')
    sock.close()
