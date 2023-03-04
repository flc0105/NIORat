import json
import logging
import queue
import socket
import struct
import threading
import time

logging.basicConfig(level=logging.DEBUG)

server = socket.socket()
server.setblocking(False)
server.bind(('', 9999))
server.listen(5)

connections = []
cmds = queue.Queue()


class Connection:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = f'{address[0]}:{address[1]}'
        self.queue = queue.Queue()
        self.status = False

    def send(self, data):
        id = int(time.time())
        data = json.dumps({
            'id': id,
            'data': data
        }).encode('utf-8')
        size = struct.pack('i', len(data))
        self.socket.send(size + data)
        return id

    def recv(self):
        pack = self.socket.recv(4)
        if pack:
            size = struct.unpack('i', pack)[0]
            if size:
                data = self.socket.recv(size)
                if data:
                    data = json.loads(data)
                    return data['id'], data['data']


def serve():
    while 1:
        try:
            conn, addr = server.accept()
            conn.setblocking(False)
            connections.append(Connection(conn, addr))
            logging.info('连接建立：{}'.format(addr))
        except BlockingIOError:
            pass
        except:
            logging.error('连接建立异常', exc_info=True)

        for conn in connections:
            try:
                id, data = conn.recv()
                if id:
                    if conn.status and (cmds.empty() or id != cmds.get()):
                        logging.info(data)
                    else:
                        conn.queue.put((id, data))
                else:
                    logging.error(f'连接断开：{conn.address}')
                    connections.remove(conn)
            except BlockingIOError:
                pass
            except ConnectionResetError:
                logging.error(f'连接断开：{conn.address}')
                connections.remove(conn)
            except:
                logging.error('接收异常', exc_info=True)


threading.Thread(target=serve, daemon=True).start()

while 1:
    cmd = input('flc > ')
    if not cmd.strip():
        pass
    elif cmd == 'ls':
        for i, conn in enumerate(connections):
            print(f'{i}\t{conn.address}')
    else:
        conn = None
        try:
            i = int(cmd)
            if connections[i]:
                conn = connections[i]
        except:
            print('无效选项')

        if conn:
            while not conn.queue.empty():
                print('未读消息：' + conn.queue.get()[1])
            while 1:
                try:
                    conn.status = True
                    cmd = input(f'{conn.address} > ')
                    if not cmd.strip():
                        continue
                    if cmd == 'bg':
                        break
                    id = conn.send(cmd)
                    cmds.put(id)
                    print(conn.queue.get()[1])
                except ConnectionResetError:
                    break
                except Exception as e:
                    print(e)
            conn.status = False
