import queue
import threading
import time

from auxiliaries import *
import numpy as np
import ipaddress
from ip import IP, IP_TYPE, ICMP_TYPE, TCP_TYPE
from ipaddress import ip_address


# UDP structure
# | SRC port(2) | DEST port(2) | payload |

# TCP structure
# | SRC port(2) | DEST port(2) | TYPE(1) | payload |


class Aocket(object):
	"""docstring for Aocket"""
	def __init__(self, **kwargs):
		super(Aocket, self).__init__()
		self._ip = IP(**kwargs)
		self._icmp_queue = queue.Queue()
		self._bind = {}
		self._recv_thread = threading.Thread(target=self._recv_all, daemon=True)
		self._stop_working = threading.Event()
		self._ping_tick = 0

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, t, v, tb):
		self.shutdown()

	def start(self):
		self._ip.start()
		self._recv_thread.start()

	def shutdown(self):
		self._stop_working.set()
		self._recv_thread.join()
		self._ip.shutdown()

	def _gen_ping_id(self):
		self._ping_tick = (self._ping_tick+1)%256
		return self._ping_tick

	def ping(self, src, dst, content, timeout=4):
		ping_id = self._gen_ping_id()
		payload = np.concatenate((convi2b(ICMP_TYPE.PING, 1), convi2b(ping_id, 1), content))
		self._ip.send(IP_TYPE.ICMP, src, dst, payload, wait=True)
		start_time = time.time()
		end_time = start_time
		while end_time - start_time < timeout:
			try:
				src_ipaddr, dst_ipaddr, payload = self._icmp_queue.get(block=True, timeout=timeout)
			except queue.Empty:
				break
			end_time = time.time()
			src_ipaddr, dst_ipaddr = ip_address(src_ipaddr).exploded, ip_address(dst_ipaddr).exploded
			icmp_type, pong_id = payload[0], payload[1]
			if icmp_type!=ICMP_TYPE.PONG: continue
			if pong_id != ping_id: continue
			if src_ipaddr != dst: continue
			if dst_ipaddr != src: continue
			return True, end_time-start_time, payload[2:]
		return False, end_time-start_time, None


	def send(self, typ, src, dst, payload, wait=True):
		src_ipaddr, dst_ipaddr, payload = self.encapsulate_payload(typ, src, dst, payload)
		return self._ip.send(typ, src_ipaddr, dst_ipaddr, payload, wait=wait)

	def _recv_all(self):
		while not self._stop_working.is_set():
			try:
				typ, src_ipaddr, dst_ipaddr, payload = self._ip.recv(timeout=2)
			except:
				continue
			if typ==IP_TYPE.ICMP:
				icmp_type, seq_id, icmp_id = payload[0], payload[1], convb2i(payload[2:4])
				if icmp_type == ICMP_TYPE.PING: #and dst_ipaddr == self.getmyipaddr():
					print(f'Aocket received PING')
					payload[0] = ICMP_TYPE.PONG
					self._ip.send(IP_TYPE.ICMP, dst_ipaddr, src_ipaddr, payload, wait=False)
				elif icmp_type == ICMP_TYPE.PONG:
					print(f'Aocket received PONG')
					self._icmp_queue.put((src_ipaddr, dst_ipaddr, payload))
				else:
					print(f'ICMP Type {icmp_type} not supported!')

			elif typ == IP_TYPE.UDP:
				src_port, dst_port, payload = self.extract_udp_payload(payload)
				# print('Aocket received packet from', src_ipaddr, src_port)
				q = self._bind.setdefault(dst_port, queue.Queue())
				q.put((src_ipaddr, src_port, payload))

			elif typ == IP_TYPE.TCP:
				src_port, dst_port, typ, payload = self.extract_tcp_payload(payload)
				q = self._bind.setdefault(dst_port, queue.Queue())
				q.put((src_ipaddr, src_port, payload))

			else:
				print(f'Unknown aocket type: {typ}')

	def connect(self, src, dst):
		self.send(IP_TYPE.TCP, src, dst, TCP_TYPE.SYN_PAYLOAD)

	def close(self, src, dst):
		self.send(IP_TYPE.TCP, src, dst, TCP_TYPE.FIN_PAYLOAD)

	def send_tcp(self, src, dst, payload):
		self.send(IP_TYPE.TCP, src, dst, np.concatenate((TCP_TYPE.DATA_PAYLOAD, payload)))

	# Return (dst_ipaddr, dst_port, payload)
	def recv(self, port, timeout=None):
		q = self._bind.setdefault(port, queue.Queue())
		return q.get(block=True, timeout=timeout)

	def getmyipaddr(self):
		return '192.168.8.8'

	@staticmethod
	def extract_udp_payload(payload):
		return convb2i(payload[:2]), convb2i(payload[2:4]), payload[4:]

	@staticmethod
	def extract_tcp_payload(payload):
		return convb2i(payload[:2]), convb2i(payload[2:4]), payload[4], payload[5:]

	@staticmethod
	def encapsulate_payload(typ, src, dst, payload):
		if typ == IP_TYPE.UDP or typ == IP_TYPE.TCP:
			src_ipaddr, src_port = src
			dst_ipaddr, dst_port = dst
			header = np.concatenate((convi2b(src_port, 2), convi2b(dst_port, 2)))
			return src_ipaddr, dst_ipaddr, np.concatenate((header, payload))
		else:
			raise Exception("Unknown type %r" % typ)
