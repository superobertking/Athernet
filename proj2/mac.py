# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-17 21:57:47
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-18 01:11:33


from sender import Sender
from receiver import Receiver
import numpy as np
import queue

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
	def __init__(self, mtu=1500, tx_device=None, rx_device=None, max_retry=5, ack_timeout=0.2):
		super(MAC, self).__init__()
		self._mtu = mtu
		self._tx = Sender(device=tx_device)
		self._rx = Receiver(device=rx_device)
		self._tx_cnt = 0
		self._max_retry = max_retry
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
		while retry < self._max_retry:
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
			raise ValueError('Link Error: Transmit failed after {} retials'.format(self._max_retry))

	@staticmethod
	def _convi2b(tx_cnt, bytes):
		return np.array([(tx_cnt >> (8*(bytes-i-1))) & 0xff for i in range(bytes)], dtype=np.uint8)

	@staticmethod
	def _convb2i(buffer):
		data = 0
		for x in buffer:
			data = (data << 8) | x
		return data

	def send(self, packet):
		self._tx_cnt += 1
		packet_id = self._convi2b(self._tx_cnt, 4)
		packet_length = self._convi2b(len(packet), 4)

		# max fragment unit
		mfu = self._mtu - MAC_DATA_HEADER_LEN
		frame_cnt = len(packet) // mfu + int(len(packet) % mfu != 0)

		print('frame_cnt is', frame_cnt)

		print('sending start')
		self._stop_and_wait(np.concatenate((
			MAC_FRAME_TYPE.CTRL_START,
			packet_id, packet_length,
			np.array([frame_cnt], dtype=np.uint8)
		)))
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
		if data.size != 10 or data[0] != MAC_FRAME_TYPE.CTRL_START[0]:
			raise ValueError('Wrong CTRL_START data length')
		return klass._convb2i(data[1:5]), klass._convb2i(data[5:9]), data[9]

	@classmethod
	def _extract_data(klass, data):
		if data.size < 2 or data[0] != MAC_FRAME_TYPE.DATA[0]:
			raise ValueError('Wrong DATA data length', data[0])
		return data[1], data[2:]

	@classmethod
	def _extract_end(klass, data):
		if data.size != 5 or data[0] != MAC_FRAME_TYPE.CTRL_END[0]:
			raise ValueError('Wrong CTRL_END data length')
		return data[1:]

	@classmethod
	def _extract_ack(klass, data):
		if data.size != 2 or data[0] != MAC_FRAME_TYPE.ACK[0]:
			raise ValueError('Wrong ACK data length')
		return True

	def recv(self):
		print('waiting start')
		packet_id, packet_length, frame_cnt = self._extract_start(self._rx.recv())
		self._tx.send(np.concatenate((MAC_FRAME_TYPE.ACK, np.array([254], dtype=np.uint8))))
		print('received start')

		packet = []

		print('frame_cnt is', frame_cnt)

		for i in range(frame_cnt):
			print('waiting data', i)
			frame_id, data = self._extract_data(self._rx.recv())
			self._tx.send(np.concatenate((MAC_FRAME_TYPE.ACK, np.array([frame_id], dtype=np.uint8))))
			packet.append(data)
			print('received data', i)

		print('waiting end')
		packet_id_again = self._extract_end(self._rx.recv())
		self._tx.send(np.concatenate((MAC_FRAME_TYPE.ACK, np.array([255], dtype=np.uint8))))
		if packet_id != packet_id_again:
			raise ValueError('Packet ID not match')
		print('received end')

		return np.concatenate(packet)
