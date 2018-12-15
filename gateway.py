from ip import IP, IP_TYPE
from aocket import Aocket
from ipaddress import ip_address
import queue
import socket
import threading
from auxiliaries import *
import numpy as np


class Gateway(object):
	"""docstring for Gateway"""
	def __init__(self, **kwargs):
		super(Gateway, self).__init__()
		self._kwargs = kwargs
		self._ip = IP(**kwargs)
		# self._sock_nat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._sock_nat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._acoustic_work_thread = threading.Thread(target=self._acoustic_work, daemon=True)
		self._internet_work_thread = threading.Thread(target=self._internet_work, daemon=True)
		self._stop_working = threading.Event()

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, t, v, tb):
		self.shutdown()

	def start(self):
		self._ip.start()
		self._sock_nat.bind(('0.0.0.0', 10001))
		self._acoustic_work_thread.start()
		self._internet_work_thread.start()

	def shutdown(self):
		self._stop_working.set()
		self._sock_nat.close()
		self._ip.shutdown()
		self._acoustic_work_thread.join()
		self._internet_work_thread.join()

	def _acoustic_work(self):
		while not self._stop_working.is_set():
			try:
				typ, src_addr, dst_addr, data = self._ip.recv(timeout=1)
			except queue.Empty:
				continue
			if typ == IP_TYPE.UDP:
				src_port, dst_port, data = Aocket.extract_payload(data)
				print(ip_address(dst_addr).exploded, dst_port)
				self._sock_nat.sendto(data.tobytes(), (ip_address(dst_addr).exploded, dst_port))
			elif typ == IP_TYPE.ICMP:
				pass
			else:
				print("Unsupported protocol")

	def _internet_work(self):
		while not self._stop_working.is_set():
			try:
				payload, src = self._sock_nat.recvfrom(4096)
			except socket.error:
				return
			src_addr, dst_addr, payload = Aocket.encapsulate_payload(IP_TYPE.UDP, src, ('192.168.1.2', 16384), np.frombuffer(payload, dtype=np.uint8))
			self._ip.send(IP_TYPE.UDP, src_addr, dst_addr, payload)
