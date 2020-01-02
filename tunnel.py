from aocket import Aocket
import logging
import select
import threading
import socket
import struct
from socketserver import ThreadingMixIn, TCPServer, StreamRequestHandler

import argparse
import time
from datetime import datetime
import numpy as np

logging.basicConfig(level=logging.DEBUG)
SOCKS_VERSION = 5


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-r', '--recv-device', type=int_or_str,
                    help='recv device (numeric ID or substring)')
parser.add_argument('-t', '--send-device', type=int_or_str,
                    help='send device (numeric ID or substring)')
args = parser.parse_args()



aocket = Aocket(addr=0x77, rx_device=args.recv_device, tx_device=args.send_device,
            ack_timeout=0.2, max_retries=20, mtu=1500)
aocket.start()


def aocket_loop(client, local_port, ret):
    while True:
        _, _, data = aocket.recv(local_port)
        print(f'recv_data lenght {len(data)}')
        if len(data) == 0:
            client.sendall(b'')
            # client.close()
            ret[0] = 1
            break
        client.send(data.tobytes())


port_seed = 10085
def gen_port():
    global port_seed
    port_seed += 1
    return port_seed


class ThreadingTCPServer(ThreadingMixIn, TCPServer):
    pass


class SocksProxy(StreamRequestHandler):
    username = 'username'
    password = 'password'

    def handle(self):
        local_port = gen_port()
        logging.info('Accepting connection from %s:%s' % self.client_address)
        logging.info('Accepting connection at local_port %d' % local_port)

        # greeting header
        # read and unpack 2 bytes from a client
        header = self.connection.recv(2)
        version, nmethods = struct.unpack("!BB", header)

        # socks 5
        assert version == SOCKS_VERSION
        assert nmethods > 0

        # get available methods
        methods = self.get_available_methods(nmethods)

        # accept only USERNAME/PASSWORD auth
        if 2 not in set(methods):
            # close connection
            self.server.close_request(self.request)
            return

        # send welcome message
        self.connection.sendall(struct.pack("!BB", SOCKS_VERSION, 2))

        if not self.verify_credentials():
            return

        # request
        version, cmd, _, address_type = struct.unpack("!BBBB", self.connection.recv(4))
        assert version == SOCKS_VERSION

        if address_type == 1:  # IPv4
            address = socket.inet_ntoa(self.connection.recv(4))
        elif address_type == 3:  # Domain name
            domain_length = ord(self.connection.recv(1)[0])
            address = self.connection.recv(domain_length)

        port = struct.unpack('!H', self.connection.recv(2))[0]

        # reply
        try:
            if cmd == 1:  # CONNECT
                # remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote = aocket
                remote_port = port
                print('=='*20)
                remote.connect(('192.168.8.8', local_port), (address, port))
                print('=='*30)
                # bind_address = remote.getsockname()
                bind_address = ('192.168.8.8', local_port)
                # table[local_port] = self.connection
                logging.info('Connected to %s %s' % (address, port))
            else:
                self.server.close_request(self.request)

            addr = struct.unpack("!I", socket.inet_aton(bind_address[0]))[0]
            port = bind_address[1]
            reply = struct.pack("!BBBBIH", SOCKS_VERSION, 0, 0, address_type,
                                addr, port)

        except Exception as err:
            logging.error(err)
            # return connection refused error
            reply = self.generate_failed_reply(address_type, 5)

        self.connection.sendall(reply)

        # establish data exchange
        if reply[1] == 0 and cmd == 1:
            self.exchange_loop(self.connection, remote, local_port, (address, remote_port))

        self.server.close_request(self.request)

    def get_available_methods(self, n):
        methods = []
        for i in range(n):
            methods.append(ord(self.connection.recv(1)))
        return methods

    def verify_credentials(self):
        version = ord(self.connection.recv(1))
        assert version == 1

        username_len = ord(self.connection.recv(1))
        username = self.connection.recv(username_len).decode('utf-8')

        password_len = ord(self.connection.recv(1))
        password = self.connection.recv(password_len).decode('utf-8')

        if username == self.username and password == self.password:
            # success, status = 0
            response = struct.pack("!BB", version, 0)
            self.connection.sendall(response)
            return True

        # failure, status != 0
        response = struct.pack("!BB", version, 0xFF)
        self.connection.sendall(response)
        self.server.close_request(self.request)
        return False

    def generate_failed_reply(self, address_type, error_number):
        return struct.pack("!BBBBIH", SOCKS_VERSION, error_number, 0, address_type, 0, 0)

    def exchange_loop(self, client, remote, local_port, remote_addr):

        ret = [0]

        thd = threading.Thread(target=aocket_loop, args=(client, local_port, ret), daemon=True)
        thd.start()

        while True:

            # wait until client or remote is available for read
            r, w, e = select.select([client], [], [], 1)

            if client in r:
                data = client.recv(4096)
                remote.send_tcp(('192.168.8.8', local_port), remote_addr, np.frombuffer(data, dtype=np.uint8))

            if ret[0]:
                break

            # if remote in r:
            #     data = remote.recv(4096)
            #     if client.send(data) <= 0:
            #         break

        thd.join()


with ThreadingTCPServer(('127.0.0.1', 1787), SocksProxy) as server:
    server.serve_forever()

aocket.shutdown()
