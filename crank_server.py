import socket
import threading
import time
import traceback
import logging

logger = logging.getLogger('crank')
logging.basicConfig()
logger.setLevel(logging.INFO)
logger.info('start crank server.')

socket.setdefaulttimeout(10)

class Crank(object):

    def __init__(self, client_host='127.0.0.1', client_port=3456, req_host='127.0.0.1', req_port=3457):
        self.running = True
        self.client_host = client_host
        self.client_port = client_port
        self.req_host = req_host
        self.req_port = req_port
        self.clientsocket = None
        self.incomesocket = None
        self.buffer_size = 1024
        self.req_lock = threading.Lock()

    def client_thread(self, s, handler):
        if not self.running:
            s.close()
            return
        t = threading.Thread(target=handler, args=(s,))
        t.setDaemon(True)
        t.start()
        return t

    def income_client(self, s):
        logger.info('[income_client]')
        if self.clientsocket:
            s.close()
            return
        
        r = s.recv(self.buffer_size)
        if r != 'bugfeel':
            s.close()
        else:
            s.send('leefgud')
        self.clientsocket = s
        while 1:
            try:
                r = self.clientsocket.recv(self.buffer_size)
                if self.incomesocket:
                    if r == 'CONNETION_ERROR':
                        logger.info('[CONNETION_ERROR]')
                        self.incomesocket.close()
                        break
                    self.incomesocket.send(r)
                logger.info(r)
                if not r:
                    break
            except socket.timeout:
                continue
            except:
                traceback.print_exc()
                continue
        self.clientsocket = None
        logger.info('[income_client]closed')

    def income_req(self, s):
        logger.info('[income_req]')
        if not self.clientsocket:
            s.close()
            raise ValueError('clientsocket is not connected.')
        self.req_lock.acquire()
        self.incomesocket = s
        while 1:
            try:
                r = self.incomesocket.recv(self.buffer_size)
                if self.clientsocket:
                    try:
                        self.clientsocket.send(r)
                    except socket.error:
                        logger.info('[income_req]socket.error1')
                        self.incomesocket.close()
                        self.clientsocket = None
                        break
                else:
                    logger.info('[income_req]clientsocket is none, close.')
                    self.incomesocket.close()
                if not r:
                    break
                logger.info(r)
            except socket.timeout:
                continue
            except:
                traceback.print_exc()
                break
        self.incomesocket.close()
        self.incomesocket = None
        self.req_lock.release()
        logger.info('[income_req]closed')



    def listen(self, serversocket, handler):
        logger.info('start listen. handler: %s'%handler)
        while self.running:
            # accept connections from outside
            try:
                (clientsocket, address) = serversocket.accept()
                logger.info('[accept] %s:%s'%address)
                self.client_thread(clientsocket, handler)
            except socket.timeout:
                continue
        serversocket.close()
        logger.info('serversocket closed')

    def start_server(self, host, port, handler=None):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host,port))
        s.listen(5)
        server_thread = threading.Thread(target=self.listen, args=(s, handler))
        server_thread.setDaemon(True)
        server_thread.start()
        return server_thread


    def start(self):
        server_threads = []
        server_threads.append(self.start_server(self.client_host, self.client_port, self.income_client))
        server_threads.append(self.start_server(self.req_host, self.req_port, self.income_req))
        try:
            print("Serving...")
            while 1:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        self.running = False

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.client_host, self.client_port))

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.req_host, self.req_port))

        for t in server_threads:
            t.join()



crank = Crank(client_host='0.0.0.0', client_port=3456, req_port=3457)
crank.start()
