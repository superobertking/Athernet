from ip import IP, UDP, ICMP
import queue
import threading


class Gateway(object):
	"""docstring for Gateway"""
	def __init__(self, **kwargs):
		super(Gateway, self).__init__()
		self._kwargs = kwargs
	 	self._ip = IP(**kwargs)
	 	# self._sock_nat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	 	self._sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	 	self._nat_table = {}
		self._acoustic_work_thread = threading.Thead(target=self._acoustic_work, daemon=True)
		self._internet_work_thread = threading.Thead(target=self._internet_work, daemon=True)
		self._stop_working = threading.Event()

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, t, v, tb):
		self.shutdown()

	def start(self):
		self._acoustic_work_thread.start()
		self._internet_work_thread.start()

	def shutdown(self):
		self._stop_working.set()
		self._acoustic_work_thread.join()
		self._internet_work_thread.join()

	def _acoustic_work(self):
		while not self._stop_working.is_set():
			try:
				typ, src_addr, dst_addr, data = self._ip.recv(timeout=1)
			except queue.Empty:
				continue
			if typ == UDP:
				
				self._sock_send.sendto(dst_addr)
			elif typ == ICMP:
				pass

	def _internet_work(self):
		while not self._stop_working.is_set():
			pass
