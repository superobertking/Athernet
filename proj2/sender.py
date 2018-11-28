# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-17 15:43:28
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-28 03:52:15


from constants import LUT_MOD, PREAMBLE, SAMPLERATE

import sounddevice as sd
import numpy as np
import queue
from datetime import datetime
import threading
import binascii
import random
from auxiliaries import *
import reedsolo

rs_codec = reedsolo.RSCodec(4)


sd.default.latency = ('low', 'low')

class Sender(object):
	"""Sender class for physical layer"""
	def __init__(self, **kwargs):
		super(Sender, self).__init__()
		self._kwargs = kwargs
		print(kwargs)
		# self._sending_queue = queue.PriorityQueue()
		self._ctrl_queue = queue.Queue()
		self._data_queue = queue.Queue(maxsize=64)
		self._daemon_thread = threading.Thread(target=self._task, daemon=True)
		self._running = threading.Event()
		self._should_stop = threading.Event()
		self._play_buffer = np.array([], dtype=np.float32)
		self._items_sent = 0
		self._counter = 0

	def _callback(self, outdata, frames, time, status):
		if status:
			print("Error occurs %r" % status)
		while self._play_buffer.size < frames:
			if not self._ctrl_queue.empty():
				priority, payload, sent = self._ctrl_queue.get_nowait()
			elif not self._data_queue.empty():
				priority, payload, sent = self._data_queue.get_nowait()
			else:
				# print('callback go empty')
				outdata[:,0] = np.concatenate((self._play_buffer, np.zeros(frames - self._play_buffer.size, dtype=np.float32)))
				self._play_buffer = np.array([], dtype=np.float32)
				if self._should_stop.is_set():
					raise sd.CallbackStop
				return
			if payload is not None:
				self._play_buffer = np.concatenate((self._play_buffer, payload))
			if sent:
				sent.set()
			# try:
			# 	priority, payload, sent = self._sending_queue.get_nowait()
			# 	if payload is not None:
			# 		self._play_buffer = np.concatenate((self._play_buffer, payload))
			# 	if sent:
			# 		sent.set()
			# except queue.Empty:
			# 	# print('callback go empty')
			# 	outdata[:,0] = np.concatenate((self._play_buffer, np.zeros(frames - self._play_buffer.size, dtype=np.float32)))
			# 	self._play_buffer = np.array([], dtype=np.float32)
			# 	if self._should_stop.is_set():
			# 		raise sd.CallbackStop
			# 	return
		# print('callback go normoally')
		outdata[:,0] = self._play_buffer[:frames]
		self._play_buffer = self._play_buffer[frames:]

		if self._should_stop.is_set():
			raise sd.CallbackStop

	def _task(self):
		print('sender task started')

		with sd.OutputStream(samplerate=SAMPLERATE, channels=1, dtype=np.float32,
							blocksize=128,
		            		callback=self._callback, **self._kwargs):
			self._should_stop.wait()

		# with sd.OutputStream(samplerate=SAMPLERATE, channels=1, dtype=np.float32, **self._kwargs) as stream:
		# 	while True:
		# 		payload, sent = self._sending_queue.get()
		# 		if payload is not None:
		# 			stream.write(payload)
		# 		if not self._running.is_set():
		# 			print('shuting down sender')
		# 			break
		# 		if sent:
		# 			sent.set()

		# while True:
		# 	priority, payload, sent = self._sending_queue.get()
		# 	if payload is not None:
		# 		print('get payload len', len(payload))
		# 	if not self._running.is_set():
		# 		print('shuting down sender')
		# 		break
		# 	# print('timing: start sending at', datetime.now())
		# 	sd.play(payload, blocking=True, samplerate=SAMPLERATE, **self._kwargs)
		# 	# print('timing: end sending at', datetime.now())
		# 	if sent:
		# 		sent.set()


	def start(self):
		print('starting sender')
		self._running.set()
		self._daemon_thread.start()
		print('started sender')

	def shutdown(self):
		self._running.clear()
		self._should_stop.set()
		# self._sending_queue.put(((-256, 0), None, None))
		self._daemon_thread.join()

	def send(self, payload, wait=True, priority=255):
		"""\
		payload: np array of uint8
		"""
		# print(list(payload))
		if len(payload) >= 2 ** 16:
			raise ValueError('Payload length overflow')

		# priority = (priority, self._get_seq_priority())

		sent = threading.Event()
		# self._sending_queue.put((priority, self._payload2signal(payload), sent))
		queue_to_put = self._data_queue if priority == 255 else self._ctrl_queue
		queue_to_put.put((priority, self._payload2signal(payload), sent))
		if wait:
			sent.wait()
		else:
			return sent

	def send_no_queue(self, payload, wait=True):
		if len(payload) >= 2 ** 16:
			raise ValueError('Payload length overflow')

		sd.play(self._payload2signal(payload), blocking=True, samplerate=SAMPLERATE, **self._kwargs)

	def _get_seq_priority(self):
		self._items_sent += 1
		return self._items_sent

	@classmethod
	def _payload2signal(klass, payload):
		payload = payload.astype(np.uint8)
		# payload_header = np.array([(len(payload) >> 8) & 0xff, len(payload) & 0xff], dtype=np.uint8)
		payload_header = np.frombuffer(rs_codec.encode(bytes([(len(payload) >> 8) & 0xff, len(payload) & 0xff])), dtype=np.uint8)
		# crc = np.array([], dtype=np.uint8)
		crc = convi2b(binascii.crc32(bytes(payload)) & 0xffffffff, 4)
		data = np.concatenate((payload_header, payload, crc))
		# print(data)
		modulated_data = np.concatenate([klass._modulate(klass._encode(b)) for b in data])
		modulated_data = np.concatenate((PREAMBLE, modulated_data, np.zeros(8)))
		# print('after modulation:', len(payload), len(modulated_data))
		return np.array(modulated_data, dtype=np.float32)

	@staticmethod
	def _encode(data):
		return data
		# return LUT_45[data]

	@staticmethod
	def _modulate(encoded):
		# return LUT_MOD_5[encoded]
		return LUT_MOD[encoded]
