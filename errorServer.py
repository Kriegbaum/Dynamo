import socket
import atexit
import datetime

def getIP():
    ipSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ipSock.connect(('10.255.255.255', 1))
        localIP = ipSock.getsockname()[0]
    except Exception as e:
        print(e)
        print('Local IP detection failed, listening on localhost')
        localIP = '127.0.0.1'
    ipSock.close()
    return localIP

def socketKill(sock):
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()

localIP = getIP()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (localIP, 8880)
print('Initializing error server on % port %s' % server_address)
sock.bind(server_address)
sock.listen(90)
sock.settimeout(None)
atexit.register(socketKill, sock)
while True:
    connection, client_address = sock.accept()
    err = ''
    while True:
        data = connection.recv(16).decode()
        err += data
        if data:
            pass
        else:
            print(datetime.datetime.now(), err, 'recieved from', client_address)
            break
