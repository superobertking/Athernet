# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-17 15:42:10
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-17 21:44:58


from constants import *

import time
import argparse
import math
import threading
import queue
from datetime import datetime


class Receiver(object):
	"""Receiver class for physical layer"""

	class ReceiverAbort(Exception):
		pass

	def __init__(self, **kwargs):
		super(Receiver, self).__init__()
		self._kwargs = kwargs
		self._received_payload = queue.Queue()
		self._daemon_thread = threading.Thread(target=self._task, daemon=True)
		self._running = threading.Event()
		self._stopped = threading.Event()
		self._sig_recv = queue.Queue()
		self._sig_buffer = np.array([])

	def _sync_preamble(self):
		while self._sig_buffer.size < PREAMBLE_SAMPLESIZE:
			self._sig_buffer = np.concatenate((self._sig_buffer, self._sig_recv.get()))

		cursor = PREAMBLE_SAMPLESIZE
		print("read enough buffer, start sync")

		time_detach = 0
		max_rate = 0
		cursor_align = None
		found_align = False
		while not found_align:
			if not self._running.is_set():
				raise self.ReceiverAbort
			# the query will be blocked
			sig = self._sig_recv.get()
			self._sig_buffer = np.concatenate((self._sig_buffer,sig))

			for i in range(cursor, self._sig_buffer.size):
				coupling = np.dot(self._sig_buffer[i-PREAMBLE_SAMPLESIZE:i], PREAMBLE)
				power = np.sum(np.square(self._sig_buffer[i-PREAMBLE_SAMPLESIZE:i]))
				rate = coupling * coupling / power
				
				if power > 1 and rate > 60:
					time_detach = 0
					if rate > max_rate:
						max_rate = rate
						cursor_align = i
					print("big rate",rate)
				else:
					if cursor_align is None:
						continue
					time_detach += 1
					if time_detach >= 200:
						found_align = True
						break

			if cursor_align is None and self._sig_buffer.size > 10 * PREAMBLE_SAMPLESIZE:
				self._sig_buffer = self._sig_buffer[-PREAMBLE_SAMPLESIZE:]
			cursor = self._sig_buffer.size

		self._sig_buffer = self._sig_buffer[cursor_align:]

	def _extract_payload(self):
		start_time = datetime.now()
		BIAS_SELECTIONS = list(range(-1, 2))

		cursor = 0

		def _extract_byte():
			nonlocal cursor

			if not self._running.is_set():
				raise self.ReceiverAbort

			decoded_byte = 0
			for _ in range(8):
				while self._sig_buffer.size < cursor + SAMPLESIZE + max(BIAS_SELECTIONS):
					sig = self._sig_recv.get()
					self._sig_buffer = np.concatenate((self._sig_buffer, sig))

				# Calibrate PSK frequency shift
				offset_best = 0
				max_corr = 0

				for bias in BIAS_SELECTIONS:
					k = cursor + bias
					if k < 0 or k + SAMPLESIZE >= len(self._sig_buffer):
						continue

					sigsum = np.dot(self._sig_buffer[k:k+SAMPLESIZE], SIG_HI)
					if sigsum * sigsum > max_corr * max_corr:
						max_corr = sigsum
						offset_best = bias

				cursor += offset_best
				sigsum = max_corr

				div = 0

				decoded_byte = (decoded_byte << 1) | (1 if sigsum > div else 0)

				cursor += SAMPLESIZE

			if cursor > 256 * SAMPLESIZE:
				self._sig_buffer = self._sig_buffer[cursor + min(BIAS_SELECTIONS):]
				cursor = -min(BIAS_SELECTIONS)

			return decoded_byte

		payload_length = (_extract_byte() << 8) | _extract_byte()
		print('payload_length is', payload_length)
		payload = [_extract_byte() for _ in range(payload_length)]

		self._sig_buffer = self._sig_buffer[cursor:]

		end_time = datetime.now()
		print(end_time - start_time)

		return np.array(payload, dtype=np.uint8)

	def _task(self):
		try:
			with sd.InputStream(callback=self._receive_signal, samplerate=SAMPLERATE,
								channels=1, **self._kwargs):
				while self._running.is_set():
					self._sync_preamble()
					payload = self._extract_payload()
					self._received_payload.put(payload)
		except self.ReceiverAbort:
			pass

	def start(self):
		self._running.set()
		self._daemon_thread.start()

	def shutdown(self):
		self._running.clear()
		self._daemon_thread.join()

	def recv(self, timeout=None):
		return self._received_payload.get(timeout=timeout)

	def _receive_signal(self, indata, frames, time, status):
		if status:
			print("Error occurs %r" % status)
		data_reshape = np.array(indata[:,0])
		self._sig_recv.put(data_reshape)
