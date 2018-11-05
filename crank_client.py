import socket
import threading
import time
import traceback
import sys
import logging

logger = logging.getLogger('crank')
logging.basicConfig()
logger.setLevel(logging.INFO)
logger.info('start crank client.')
socket.setdefaulttimeout(10)


class CrankClient(object):

    def __init__(self, server_address, local_address):
        self.running = True
        self.server_address = server_address
        self.local_address = local_address
        self.clientsocket = None
        self.outcomesocket = None
        self.buffer_size = 1024

    def outcome_listener(self):
        logger.info('[outcome_listener]')
        while self.running:
            if not self.outcomesocket:
                time.sleep(0.1)
                continue
            try:
                r = self.outcomesocket.recv(self.buffer_size)
                if self.clientsocket:
                    self.clientsocket.send(r)
                logger.info(r)
                if not r:
                    self.outcomesocket.close()
                    self.outcomesocket = None
                    continue
            except socket.timeout:
                continue
            except:
                traceback.print_exc()
                continue
        self.outcomesocket = None
        logger.info('[outcome_listener]closed')

    def clientsocket_listener(self):
        logger.info('[clientsocket_listener]')
        
        while self.running:
            try:
                try:
                    r = self.clientsocket.recv(self.buffer_size)
                except socket.timeout:
                    continue

                try:
                    if not self.outcomesocket:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect(self.local_address)
                        self.outcomesocket = s

                    if self.outcomesocket:
                        self.outcomesocket.send(r)
                except:
                    break
                logger.info(r)
                if not r:
                    break
            except socket.timeout:
                break
            except:
                traceback.print_exc()
                break
        self.clientsocket.send('CONNETION_ERROR')
        self.clientsocket.close()
        self.clientsocket = None
        logger.info('[clientsocket_listener]closed')
        sys.exit(0)
        


    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.server_address)
        self.clientsocket = s

        r = self.clientsocket.send('bugfeel')
        r = self.clientsocket.recv(self.buffer_size)
        if r != 'leefgud':
            print('wrong server')
            sys.exit(1)
        
        t2 = threading.Thread(target=self.outcome_listener)

        t2.setDaemon(True)
        t2.start()
        self.clientsocket_listener()

        self.running = False
        if self.clientsocket:
            self.clientsocket.close()



crank = CrankClient(('127.0.0.1', 3456), ('127.0.0.1', 8000))
crank.start()
