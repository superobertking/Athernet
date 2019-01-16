from ip import IP, IP_TYPE, ICMP_TYPE
from aocket import Aocket
from ipaddress import ip_address
import queue
import struct
import os
import socket
import time
import threading
import fcntl
from auxiliaries import *
import numpy as np

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0


class Gateway(object):
	"""docstring for Gateway"""
	def __init__(self, **kwargs):
		super(Gateway, self).__init__()
		self._kwargs = kwargs
		self._ip = IP(**kwargs)
		self._nat_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._icmp_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
		# self._icmp_sock.setsockopt(socket.SOL_IP, socket.IP_TTL, 1)
		# self._icmp_sock.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
		# fcntl.fcntl(self._icmp_sock, fcntl.F_SETFL, os.O_NONBLOCK)
		self._acoustic_work_thread = threading.Thread(target=self._acoustic_work, daemon=True)
		self._nat_work_thread = threading.Thread(target=self._nat_work, daemon=True)
		self._icmp_work_thread = threading.Thread(target=self._icmp_work, daemon=True)
		self._icmp_id = os.getpid() & 0xFFFF
		self._stop_working = threading.Event()

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, t, v, tb):
		self.shutdown()

	def start(self):
		self._ip.start()
		self._nat_sock.bind(('0.0.0.0', 10001))
		self._acoustic_work_thread.start()
		self._nat_work_thread.start()
		self._icmp_work_thread.start()

	def shutdown(self):
		self._stop_working.set()
		self._nat_sock.close()
		self._icmp_sock.close()
		self._ip.shutdown()
		self._acoustic_work_thread.join()
		self._nat_work_thread.join()
		self._icmp_work_thread.join()

	def _acoustic_work(self):
		while not self._stop_working.is_set():
			try:
				typ, src_addr, dst_addr, payload = self._ip.recv(timeout=1)
			except queue.Empty:
				continue
			src_addr, dst_addr = ip_address(src_addr).exploded, ip_address(dst_addr).exploded
			if typ == IP_TYPE.UDP:
				src_port, dst_port, payload = Aocket.extract_payload(payload)
				print(dst_addr, dst_port)
				self._nat_sock.sendto(payload.tobytes(), (dst_addr, dst_port))
			elif typ == IP_TYPE.ICMP:
				icmp_type, seq_id, icmp_id = payload[0], payload[1], convb2i(payload[2:4])
				if icmp_type == ICMP_TYPE.PING:
					self._send_one_icmp(ICMP_ECHO_REQUEST, dst_addr, seq_id, payload[2:].tobytes(), icmp_id)
				elif icmp_type == ICMP_TYPE.PONG:
					self._send_one_icmp(ICMP_ECHO_REPLY, dst_addr, seq_id, payload[2:].tobytes(), icmp_id)
			else:
				print("Unsupported protocol")

	def _nat_work(self):
		while not self._stop_working.is_set():
			try:
				payload, src = self._nat_sock.recvfrom(4096)
			except socket.error:
				return
			src_addr, dst_addr, payload = Aocket.encapsulate_payload(IP_TYPE.UDP, src, ('192.168.1.2', 16384), np.frombuffer(payload, dtype=np.uint8))
			self._ip.send(IP_TYPE.UDP, src_addr, dst_addr, payload)

	def _icmp_work(self):
		while not self._stop_working.is_set():
			try:
				recPacket, src = self._icmp_sock.recvfrom(4096)
			except socket.error as e:
				print(e)
				time.sleep(1)
				continue

			icmp_type, code, _, packetID, seq_id = struct.unpack("!bbHHh", recPacket[20:28])
			# seq_id >>= 8
			print(f'Gateway received std ICMP packet from {src} with icmp_type {icmp_type} code {code} and seq_id {seq_id}')
			print(f"packetID: {packetID} ; self._icmp_id: {self._icmp_id} ; recP[28]={recPacket[28]}")

			# Filters out the echo request itself. 
			# This can be tested by pinging 127.0.0.1 
			# You'll see your own request
			if icmp_type == ICMP_ECHO_REQUEST and code==0:
				forward_icmp_type = ICMP_TYPE.PING
			elif icmp_type == ICMP_ECHO_REPLY and code==0 and packetID==self._icmp_id:
				forward_icmp_type = ICMP_TYPE.PONG
			else:
				continue

			# convert the byte order
			payload = np.concatenate((convi2b(forward_icmp_type, 1), convi2b(seq_id, 1), convi2b(packetID, 2), np.frombuffer(recPacket[28:][::-1], dtype=np.uint8)))

			self._ip.send(IP_TYPE.ICMP, src[0], '192.168.1.2', payload)

	# Reference https://github.com/samuel/python-ping/blob/master/ping.py

	def _send_one_icmp(self, std_icmp_type, dest_addr, seq_id, data, icmp_id):
		data = data[::-1]
		dest_addr = socket.gethostbyname(dest_addr)
		# Header is type (8), code (8), checksum (16), id (16), sequence (16)
		my_checksum = 0
		# Make a dummy heder with a 0 checksum.
		header = struct.pack("!bbHHh", std_icmp_type, 0, my_checksum, icmp_id, seq_id)
		# Calculate the checksum on the data and the dummy header.
		my_checksum = self.icmp_checksum(header + data)
		# Now that we have the right checksum, we put that in. It's just easier
		# to make up a new header than to stuff it into the dummy.
		tt = socket.htons(my_checksum)
		print("------------------", tt);
		header = struct.pack(
			"!bbHHh", std_icmp_type, 0, ((tt&0xff)<<8)|(tt>>8), icmp_id, seq_id
		)
		packet = header + data
		print(f'ICMP sending packet {packet} to {dest_addr}')
		self._icmp_sock.sendto(packet, (dest_addr, 1)) # Don't know about the 1

	@staticmethod
	def icmp_checksum(source_string):
		sum = 0
		countTo = (len(source_string)/2)*2
		count = 0
		while count < countTo:
			thisVal = source_string[count + 1]*256 + source_string[count]
			sum = sum + thisVal
			sum = sum & 0xffffffff # Necessary?
			count = count + 2

		if countTo < len(source_string):
			sum = sum + source_string[len(source_string) - 1]
			sum = sum & 0xffffffff # Necessary?

		sum = (sum >> 16)  +  (sum & 0xffff)
		sum = sum + (sum >> 16)
		answer = ~sum
		answer = answer & 0xffff

		# Swap bytes. Bugger me if I know why.
		answer = answer >> 8 | (answer << 8 & 0xff00)

		return answer
