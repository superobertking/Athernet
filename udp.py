from auxiliaries import *
import numpy as np
import ipaddress
from ip import IP


class UDP(object):
	"""docstring for UDP"""
	def __init__(self, **kwargs):
		super(UDP, self).__init__()
		self._ip = IP(**kwargs)

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, t, v, tb):
		self.shutdown()

	def start(self):
		self._ip.start()

	def shutdown(self):
		self._ip.shutdown()

	def send(self, src, dst, payload, wait=True):
		ip_payload = np.concatenate((convi2b(src[1], 2), convi2b(dst[1], 2), payload))
		return self._ip.send(src[0], dst[0], ip_payload, wait=wait)

	def recv(self, timeout=None):
		src_addr, dst_addr, data = self._ip.recv(timeout=timeout)
		return (src_addr, convb2i(data[:2])), (dst_addr, convb2i(data[2:4])), data[4:]

	@static_method
	def extract_payload(payload):
		return convb2i(payload[:2]), convb2i(payload[2:4]), payload[4:]
