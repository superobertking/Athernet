class Host(object):
	"""docstring for Host"""
	def __init__(self, gateway_addr):
		super(Host, self).__init__()
		self._gateway_addr = gateway_addr
		self._mac = MAC(**kwargs)
		self._acoustic_work_thread = threading.Thead(target=self._acoustic_work, daemon=True)
		self._stop_working = threading.Event()

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, t, v, tb):
		self.shutdown()

	def start(self):
		self._mac.start()

	def shutdown(self):
		self._stop_working.set()
		self._mac.shutdown()

	def send(self, addr, ):
