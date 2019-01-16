from auxiliaries import *
import numpy as np
from mac import MAC
from ipaddress import ip_address


# PROTOCOL(1B) SRC_ADDR(4B) DST_ADDR(4B)
class IP_TYPE:
	RESERVED = 0
	ICMP = 1
	TCP = 2
	UDP = 3

# ICMP structure
# | payload |
# payload structure
# | type(1) | id(1) | payload |
class ICMP_TYPE:
	PING = 0
	PONG = 3

class TCP_TYPE:
	SYN = 0
	ACK = 1
	FIN = 2
	DATA = 3

for name in ['SYN', 'ACK', 'FIN', 'DATA']:
	setattr(TCP_TYPE, name + '_PAYLOAD', np.array([getattr(TCP_TYPE, name)], dtype=np.uint8))


class IP(object):
	"""docstring for IP"""
	def __init__(self, **kwargs):
		super(IP, self).__init__()
		self._mac = MAC(**kwargs)
		self._arp = {'192.168.8.8': 0x77, '202.120.58.157': 0xee}

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, t, v, tb):
		self.shutdown()

	def start(self):
		self._mac.start()

	def shutdown(self):
		self._mac.shutdown()

	def send(self, typ, src_addr, dst_addr, payload, wait=True):
		ip_header = np.array([typ], dtype=np.uint8)
		ip_header = np.concatenate((ip_header, np.frombuffer(ip_address(src_addr).packed + ip_address(dst_addr).packed, dtype=np.uint8)))
		print('IP send payload length:', len(payload))
		print('ARP', self._arp[dst_addr])
		return self._mac.send(self._arp[dst_addr], np.concatenate((ip_header, payload)), wait=wait)

	def recv(self, timeout=None):
		data = self._mac.recv(timeout=timeout)
		print('IP received packet')
		return data[0], data[1:5].tobytes(), data[5:9].tobytes(), data[9:]
