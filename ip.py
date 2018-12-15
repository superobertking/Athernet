from auxiliaries import *
import numpy as np
from mac import MAC
from ipaddress import ipaddress


# PROTOCOL(1B) SRC_ADDR(4B) DST_ADDR(4B)
class IP_TYPE:
	RESERVED = 0
	ICMP = 1
	TCP = 2
	UDP = 3


class IP(object):
	"""docstring for IP"""
	def __init__(self, **kwargs):
		super(IP, self).__init__()
		self._mac = MAC(**kwargs)

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
		ip_header = np.concatenate((ip_header, np.frombuffer(ipaddress(src_addr).packed + ipaddress(dst_addr).packed, dtype=np.uint8)))
		return self._mac.send(0xff, np.concatenate((ip_header, payload)), wait=wait)

	def recv(self, timeout=None):
		data = self._mac.recv(timeout=timeout)
		return data[0], convb2i(data[1:5]), convb2i(data[5:9]), data[9:]
