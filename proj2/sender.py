# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-17 15:43:28
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-17 20:07:59


from constants import LUT_MOD, PREAMBLE, SAMPLERATE

import sounddevice as sd
import numpy as np
import queue
import threading


class Sender(object):
	"""Sender class for physical layer"""
	def __init__(self, **kwargs):
		super(Sender, self).__init__()
		self._kwargs = kwargs
		print(kwargs)
		self._sending_queue = queue.Queue()
		self._daemon_thread = threading.Thread(target=self._task, daemon=True)
		self._running = threading.Event()
		self._stopped = threading.Event()

	def _task(self):
		while True:
			payload, sent = self._sending_queue.get()
			if not self._running.is_set():
				break

			modulated_data = self._payload2signal(payload)

			sd.play(modulated_data, blocking=True, samplerate=SAMPLERATE, **self._kwargs)
			if sent:
				sent.set()

	def start(self):
		self._running.set()
		self._daemon_thread.start()

	def shutdown(self):
		self._running.clear()
		self._sending_queue.put((None, None))
		self._daemon_thread.join()

	def send(self, payload, wait=True):
		"""\
		payload: np array of uint8
		"""
		print(list(payload))
		if len(payload) >= 2 ** 16:
			raise ValueError('Payload length overflow')

		sent = threading.Event() if wait else None
		self._sending_queue.put((payload[:], sent))
		if wait:
			sent.wait()

	@classmethod
	def _payload2signal(klass, payload):
		payload_header = np.array([(len(payload) >> 8) & 0xff, len(payload) & 0xff], dtype=np.uint8)
		crc = np.array([], dtype=np.uint8)
		# data = np.concatenate((payload, crc))
		data = np.concatenate((payload_header, payload, crc))
		print(data)
		modulated_data = np.concatenate([klass._modulate(klass._encode(b)) for b in data])
		modulated_data = np.concatenate((PREAMBLE, modulated_data))
		return modulated_data

	@staticmethod
	def _encode(data):
		return data
		# return LUT_45[data]

	@staticmethod
	def _modulate(encoded):
		# return LUT_MOD_5[encoded]
		return LUT_MOD[encoded]
