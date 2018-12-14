# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-17 21:57:47
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-28 01:02:00


from sender import Sender
from receiver import Receiver
import numpy as np
import queue
import time
from datetime import datetime
from auxiliaries import *
import threading

MAC_HEADER_LEN = 5

TYPES = ['ACK', 'START', 'DATA', 'PING', 'PONG']
class MACTYPE:
	pass

for i, t in enumerate(TYPES):
	setattr(MACTYPE, t, i)

# START    : DST (1B) SRC (1B) TYPE (1B) FRAME_ID (2B) FRAME_CNT (1B)
# DATA     : DST (1B) SRC (1B) TYPE (1B) FRAME_ID (2B) PAYLOAD(-MTU)
# ACK      : DST (1B) SRC (1B) TYPE (1B) FRAME_ID (2B)
# PING     : DST (1B) SRC (1B) TYPE (1B) FRAME_ID (2B)
# PONG     : DST (1B) SRC (1B) TYPE (1B) FRAME_ID (2B)

class MAC(object):
	"""MAC class using physical link classes"""
	def __init__(self, addr=1, mtu=1500, tx_device=None, rx_device=None, max_retries=5, ack_timeout=0.2):
		super(MAC, self).__init__()
		self._mtu = mtu
		self._addr = addr
		self._tx = Sender(device=tx_device)
		self._rx = Receiver(device=rx_device)
		self._tx_cnt = 0
		self._max_retries = max_retries
		self._ack_timeout = ack_timeout
		self._received_packets = []
		self._ack_queue = queue.Queue()
		self._pong_queue = queue.Queue()
		self._net_queue = queue.Queue()
		self._frame_tick = 0
		self._work_thread = threading.Thread(target=self._work, daemon=True)
		self._stop_working = threading.Event()

	def __enter__(self):
		self.start()
		return self
	
	def __exit__(self, t,v,tb):
		self.shutdown()

	def start(self):
		self._rx.start()
		self._tx.start()
		self._work_thread.start()

	def shutdown(self):
		self._stop_working.set()
		self._work_thread.join()
		self._rx.shutdown()
		self._tx.shutdown()

	@staticmethod
	def _symbol(i):
		return np.array([i], dtype=np.uint8)

	@staticmethod
	def _extract_frame(frame):
		if frame.size < MAC_HEADER_LEN:
			return None, None, None, None, None
		return frame[0], frame[1], frame[2], convb2i(frame[3:5]), frame[5:]

	@staticmethod
	def _is_type(frame, mac_type):
		if frame.size < MAC_HEADER_LEN:
			return False
		if mac_type == MACTYPE.DATA:
			return frame[2] == MACTYPE.DATA
		if mac_type == MACTYPE.ACK:
			return frame[2] == MACTYPE.ACK
		if mac_type == MACTYPE.START:
			return frame.size == MAC_HEADER_LEN + 1 and frame[2] == MACTYPE.START
		if mac_type == MACTYPE.PING:
			return frame[2] == MACTYPE.PING
		if mac_type == MACTYPE.PONG:
			return frame[2] == MACTYPE.PONG
		return False

	def _gen_frame_id(self, cnt=1):
		self._frame_tick += cnt
		return range(self._frame_tick - cnt, self._frame_tick)

	def _work(self):
		# packet_buffer = np.array([], np.uint8)

		class STATE:
			pass
		for i, name in enumerate(['GET_START', 'GET_DATA']):
			setattr(STATE, name, i)

		state = STATE.GET_START

		# last_frame_id = -1
		frame_cnt = 0

		frame_id_map = {}

		while not self._stop_working.is_set():
			try:
				frame = self._rx.recv(timeout=1)
				dst, src, mac_type, frame_id, payload = self._extract_frame(frame)
			except queue.Empty:
				dst = None
			if self._stop_working.is_set():
				break
			if dst != self._addr:
				continue
			print('in _work, get frame_id', frame_id)
			if self._is_type(frame, MACTYPE.DATA):
				print('in _work, get data frame_id', frame_id)
				for _ in range(6):
					self._send_ack(src, frame_id, wait=False, priority=-2)
				if state != STATE.GET_DATA:
					continue
				if frame_id in frame_id_map:
					continue
				# last_frame_id = frame_id
				# packet_buffer = np.concatenate((packet_buffer, payload))
				frame_id_map[frame_id] = payload
				if len(frame_id_map) == frame_cnt:
					self._net_queue.put(np.concatenate([frame_id_map[i] for i in sorted(frame_id_map.keys())]))
					state = STATE.GET_START
			elif self._is_type(frame, MACTYPE.START):
				print('in _work, get start frame_id', frame_id)
				for _ in range(6):
					self._send_ack(src, frame_id, wait=False, priority=-2)
				if state != STATE.GET_START:
					continue
				frame_cnt = convb2i(payload)
				# last_frame_id = frame_id
				# packet_buffer = np.array([], np.uint8)
				state = STATE.GET_DATA
				frame_id_map = {}
			elif self._is_type(frame, MACTYPE.ACK):
				print('in _work, get ack frame_id', frame_id)
				self._ack_queue.put((src, frame_id))
			elif self._is_type(frame, MACTYPE.PING):
				# print('timing: received PING at', datetime.now())
				self._send_pong(src, frame_id, wait=False)
			elif self._is_type(frame, MACTYPE.PONG):
				# print('timing: received PONG at', datetime.now())
				self._pong_queue.put((src, frame_id))
			else:
				pass
		print('_work exited')

	def _stop_and_wait(self, dst, mac_type, frame_id, payload):
		retry = 0
		while retry < self._max_retries:
			retry += 1
			print('trial {} start'.format(retry))
			self._send_frame(dst, mac_type, frame_id, payload)
			print('trial {} sent'.format(retry))
			try:
				print('trial {} receiving'.format(retry))
				while True:
					src, ack_frame_id = self._ack_queue.get(timeout=self._ack_timeout)
					if ack_frame_id == frame_id:
						break
				print('trial {} received'.format(retry))
				break
			except queue.Empty:
				print('trial {} timed out'.format(retry))
				continue
		else:
			raise ValueError('Link Error: Transmit failed after {} retials'.format(self._max_retries))

	def _send_frame(self, dst, mac_type, frame_id, payload=np.array([], dtype=np.uint8), **kwargs):
		return self._tx.send(np.concatenate((
			np.array([dst, self._addr, mac_type], dtype=np.uint8),
			convi2b(frame_id, 2), payload
		)), **kwargs)

	def _send_ack(self, dst, frame_id, **kwargs):
		return self._send_frame(dst, MACTYPE.ACK, frame_id, **kwargs)

	def _send_ping(self, dst, frame_id, **kwargs):
		return self._send_frame(dst, MACTYPE.PING, frame_id, **kwargs)

	def _send_pong(self, dst, frame_id, **kwargs):
		return self._send_frame(dst, MACTYPE.PONG, frame_id, **kwargs)

	def ping(self, dst, timeout=1):
		frame_id = self._gen_frame_id()[0]		
		start_time = datetime.now()
		self._send_ping(dst, frame_id)
		while True:
			src, pong_frame_id = self._pong_queue.get(timeout=timeout)
			if frame_id == pong_frame_id:
				break
		end_time = datetime.now()
		return end_time - start_time

	def perf(self, dst):
		frame_id = self._gen_frame_id()[0]
		mfu = self._mtu - MAC_HEADER_LEN
		payload = np.random.random_integers(0, 255, size=mfu)
		start_time = datetime.now()
		self._stop_and_wait(dst, MACTYPE.DATA, frame_id, payload)
		end_time = datetime.now()
		timediff = end_time - start_time
		return mfu, timediff

	def send(self, dst, packet):
		packet_length = convi2b(len(packet), 4)

		# max fragment unit
		mfu = self._mtu - MAC_HEADER_LEN
		frame_cnt = (len(packet) + mfu - 1) // mfu
		print('frame_cnt is', frame_cnt)

		frame_id_list = list(self._gen_frame_id(frame_cnt + 1))

		# START
		print('sending start')
		self._stop_and_wait(dst, MACTYPE.START, frame_id_list[0], np.array([frame_cnt], dtype=np.uint8))
		print('sent start')

		window_size = 200

		ack_set = set()
		retry = 0
		window_set = set()
		window_list = frame_id_list[1:1 + window_size]
		window_start, window_end = 1, 1 + len(window_list)
		while retry < self._max_retries and len(ack_set) != frame_cnt:
			retry += 1
			evt = None
			for i in range(window_start, window_end):
				frame_id = frame_id_list[i]
				if frame_id in ack_set:
					continue
				fragment = packet[i * mfu : (i + 1) * mfu]
				evt = self._send_frame(dst, MACTYPE.DATA, frame_id, fragment, wait=False)
			if evt:
				evt.wait()
			time.sleep(self._ack_timeout)
			while len(window_set) != window_end - window_start:
				try:
					src, ack_frame_id = self._ack_queue.get_nowait()
					if window_start <= ack_frame_id < window_end:
						ack_set.add(ack_frame_id)
						window_set.add(ack_frame_id)
				except queue.Empty:
					print('WTF')
					break
			print('acked: ', len(ack_set), ack_set)
			print(window_list, window_set)
			if len(window_set) == len(window_list) and len(ack_set) != frame_cnt:
				window_set = set()
				window_list = frame_id_list[window_end:window_end + window_size]
				window_start, window_end = window_end, window_end + len(window_list)

		# for i, frame_id in enumerate(frame_id_list[1:]):
		# 	fragment = packet[i * mfu : (i + 1) * mfu]
		# 	print('sending frame {}'.format(frame_id))
		# 	self._stop_and_wait(dst, MACTYPE.DATA, frame_id, fragment)
		# 	print('sent frame {}'.format(frame_id))

	def recv(self, timeout=None):
		return self._net_queue.get(timeout=timeout)
