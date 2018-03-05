import socket
import sys
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 10000)
print('starting up on %s port %s' % server_address)
sock.bind(server_address)

sock.listen(1)
while True:
    print('waiting for a connection')
    connection, client_address = sock.accept()

    try:
        print('connection from', client_address)
        command = ''
        while True:
            data = connection.recv(16).decode()
            print('recieved: %s' % data)
            command += data
            if data:
                pass
            else:
                print('no more data from', client_address)
                break
        comDict = json.loads(command)
        for i in comDict:
            print(str(i) + ': ' + str(comDict[i]))
    finally:
        connection.close()
