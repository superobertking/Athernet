# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-17 21:57:47
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-18 05:21:33


from sender import Sender
from receiver import Receiver
import numpy as np
import queue
from datetime import datetime
from auxiliaries import *

MAC_DATA_HEADER_LEN = 2

class MAC_FRAME_TYPE:
	pass

for i, name in enumerate(['ACK', 'CTRL_START', 'CTRL_END', 'DATA']):
	setattr(MAC_FRAME_TYPE, name, np.array([i], dtype=np.uint8))


# CTRL_START : PACKET_ID (4B) PACKET_LENGTH (4B) FRAME_CNT (1B)
# DATA       : FRAME_ID  (1B) PAYLOAD(-MTU)
# CTRL_END   : PACKET_ID (4B)
# ACK        : ID (1B): 0-250 (DATA/FRAME_ID) 254 (START) 255 (END)

class MAC(object):
	"""MAC class using physical link classes"""
	def __init__(self, mtu=1500, tx_device=None, rx_device=None, max_retries=5, ack_timeout=0.2):
		super(MAC, self).__init__()
		self._mtu = mtu
		self._tx = Sender(device=tx_device)
		self._rx = Receiver(device=rx_device)
		self._tx_cnt = 0
		self._max_retries = max_retries
		self._ack_timeout = ack_timeout

	# def __enter__
	# def __exit__

	def start(self):
		self._rx.start()
		self._tx.start()

	def shutdown(self):
		self._rx.shutdown()
		self._tx.shutdown()

	def _stop_and_wait(self, payload):
		retry = 0
		while retry < self._max_retries:
			retry += 1
			print('trial {} start'.format(retry))
			print('trial {} sending'.format(retry))
			print(len(payload))
			self._tx.send(payload)
			print('trial {} sent'.format(retry))
			try:
				print('trial {} receiving'.format(retry))
				self._extract_ack(self._rx.recv(timeout=self._ack_timeout))
				print('trial {} received'.format(retry))
				break
			except queue.Empty:
				print('trial {} timed out'.format(retry))
				continue
		else:
			raise ValueError('Link Error: Transmit failed after {} retials'.format(self._max_retries))

	def send(self, packet):
		self._tx_cnt += 1
		packet_id = convi2b(self._tx_cnt, 4)
		packet_length = convi2b(len(packet), 4)

		# max fragment unit
		mfu = self._mtu - MAC_DATA_HEADER_LEN
		frame_cnt = len(packet) // mfu + int(len(packet) % mfu != 0)

		print('frame_cnt is', frame_cnt)

		print('sending start')
		start_payload = np.concatenate((
			MAC_FRAME_TYPE.CTRL_START,
			packet_id, packet_length,
			packet_id, packet_length,
			np.array([frame_cnt], dtype=np.uint8)
		))
		print('payload', start_payload)
		self._stop_and_wait(start_payload)
		print('sent start')

		for i in range(frame_cnt):
			fragment = packet[i*mfu:(i+1)*mfu]
			payload = np.concatenate((MAC_FRAME_TYPE.DATA, np.array([i], dtype=np.uint8), fragment))
			print('sending frame {}'.format(i))
			self._stop_and_wait(payload)
			print('sent frame {}'.format(i))

		print('sending end')
		self._stop_and_wait(np.concatenate((MAC_FRAME_TYPE.CTRL_END, packet_id)))
		print('sent end')

	@classmethod
	def _extract_start(klass, data):
		print('received canary', data[1:9])
		data = np.concatenate((data[:1], data[9:]))
		if not klass._is_start(data):
			return (None, None, None)
		return convb2i(data[1:5]), convb2i(data[5:9]), data[9]

	@classmethod
	def _extract_data(klass, data):
		if not klass._is_data(data):
			return (None, None)
		return data[1], data[2:]

	@classmethod
	def _extract_end(klass, data):
		if not klass._is_end(data):
			return None
		return convb2i(data[1:])

	@classmethod
	def _extract_ack(klass, data):
		print(data, data.size)
		if not klass._is_ack(data):
			return False
		return True

	@classmethod
	def _is_ack(klass, data):
		return data.size == 2 and data[0] == MAC_FRAME_TYPE.ACK[0]

	@classmethod
	def _is_data(klass, data):
		return data.size >= 2 and data[0] == MAC_FRAME_TYPE.DATA[0]

	@classmethod
	def _is_start(klass, data):
		return data.size == 10 and data[0] == MAC_FRAME_TYPE.CTRL_START[0]

	@classmethod
	def _is_end(klass, data):
		return data.size == 5 and data[0] == MAC_FRAME_TYPE.CTRL_END[0]

	@classmethod
	def _is_valid(klass, data):
		return klass._is_data(data) or klass._is_ack(data) or klass._is_start(data) or klass._is_end(data)

	def recv(self):

		packet_id = None
		while packet_id is None:
			print('waiting start')
			start_pack = self._rx.recv()
			print(start_pack)
			packet_id, packet_length, frame_cnt = self._extract_start(start_pack)
		self._tx.send(np.concatenate((MAC_FRAME_TYPE.ACK, np.array([254], dtype=np.uint8))))
		print('received start')

		start_time = datetime.now()

		packet = []

		print('frame_cnt is', frame_cnt)

		frame_id = 0
		while True:
			print('waiting data', i)
			received_frame = self._rx.recv()
			if self._is_end(received_frame):
				break
			if self._is_start(received_frame):
				self._tx.send(np.concatenate((MAC_FRAME_TYPE.ACK, np.array([254], dtype=np.uint8))))
				print('Sent start ack again')
			elif self._is_data(received_frame):
				frame_id, data = self._extract_data(received_frame)
				self._tx.send(np.concatenate((MAC_FRAME_TYPE.ACK, np.array([frame_id], dtype=np.uint8))))
				packet.append(data)
				print('received data', frame_id)

		# print('waiting end')
		packet_id_again = self._extract_end(received_frame)
		self._tx.send(np.concatenate((MAC_FRAME_TYPE.ACK, np.array([255], dtype=np.uint8))))
		if packet_id != packet_id_again:
			raise ValueError('Packet ID not match')
		print('received end')


		end_time = datetime.now()

		print(end_time - start_time)
		
		return np.concatenate(packet)
