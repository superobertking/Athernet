import re
import numpy as np
import sys
import argparse
from auxiliaries import *
from aocket import Aocket
from ip import IP_TYPE


PARSE_CMD = re.compile(r'^(?P<cmd>USER|PASS|PWD|CWD|PASV|LIST|RETR)\s*(\s(?P<args>.*))?$')
PARSE_RESP = re.compile(r'^(?P<code>\d+)\s*(\s+(?P<info>.*))?$')
U8_PAT = r'[1-9]?\d|1\d\d|2[0-4]\d|25[0-5]'
PASV_ADDR = re.compile(fr'\((?P<ip>(({U8_PAT}),){{3}}({U8_PAT})),(?P<port>({U8_PAT}),({U8_PAT}))\)')
RETR_FILENAME = re.compile(r'(\S+)')
FILE_SIZE = re.compile(r'\((?P<size>\d+) bytes?\)')


class FTP(object):
	"""FTP class"""

	def __init__(self, dst, *args, **kwargs):
		super(FTP, self).__init__()
		self._aocket = Aocket(*args, **kwargs)
		self._src = ('192.168.8.8', 10021)
		self._dst = dst
		self._connected = False
		self._pasv_addr = None
		self._pasv_conn = None
		self._pasv_resp = b''
		self._recv_buf = b''
		self._pasv_port_seed = 10085

	def __enter__(self):
		self._aocket.start()
		self._aocket.connect(self._src, self._dst)
		self._connected = True
		self._print(self._recv())
		return self

	def __exit__(self, t, v, tb):
		self._aocket.shutdown()
		# send QUIT
		pass

	@staticmethod
	def _print(s):
		print(f'< {s}')

	def _send(self, cmd):
		self._aocket.send_tcp(self._src, self._dst, np.frombuffer((cmd + '\n').encode(), dtype=np.uint8))

	def _recv(self):
		pos = self._recv_buf.find(b'\n')
		while pos == -1:
			src_ip, src_port, recv_ctt = self._aocket.recv(self._src[1])
			if len(recv_ctt) == 0:
				break
			self._recv_buf += recv_ctt.tobytes()
			pos = self._recv_buf.find(b'\n')
		if pos != -1:
			ret, self._recv_buf = self._recv_buf[:pos], self._recv_buf[pos+1:]
		else:
			ret, self._recv_buf = self._recv_buf, b''

		return ret.decode().strip('\r\n')

	def connected(self):
		return self._connected

	def disconnect(self):
		if self._connected:
			self._aocket.close(src, dst)
			self._connected = False

	def _gen_pasv_port(self):
		self._pasv_port_seed += 1
		return self._pasv_port_seed

	def _start_conn(self, dst):
		if self._pasv_conn is None:
			self._pasv_conn = (self._src[0], self._gen_pasv_port())
			self._aocket.connect(self._pasv_conn, dst)

	def _get_resp(self, filename, size):
		while True:
			src_ip, src_port, ctt = self._aocket.recv(self._pasv_conn[1])
			if len(ctt) == 0:
				break
			self._pasv_resp += ctt.tobytes()
			if size == len(self._pasv_resp):
				break
		with open(filename, 'wb') as f:
			f.write(self._pasv_resp)
		self._pasv_conn = None
		self._pasv_resp = b''

	def do(self, cmd):
		parse_res = PARSE_CMD.match(cmd)
		if parse_res is None:
			print('Wrong command format!')
			return

		self._send(cmd)

		if parse_res['cmd'] == 'QUIT':
			resp = self._recv()
			self._print(resp)
			self.disconnect()
		elif parse_res['cmd'] == 'PASV':
			resp = self._recv()
			self._print(resp)
			resp_res = PARSE_RESP.match(resp)
			if resp_res is None:
				print('Error response format!', file=sys.stderr)
				return
			if resp_res['code'] != '227':
				return

			info = resp_res['info']
			pasv_addr = PASV_ADDR.search(info)
			if pasv_addr is None:
				print('Error response format!', file=sys.stderr)
				return
			assert(pasv_addr['ip'] is not None and pasv_addr['port'] is not None)

			pasv_ip = pasv_addr['ip'].replace(',', '.')
			pasv_port = convb2i(map(int, pasv_addr['port'].split(',')))
			self._pasv_addr = (pasv_ip, pasv_port)

		elif parse_res['cmd'] in ['LIST', 'RETR']:

			if self._pasv_addr:
				self._start_conn(self._pasv_addr)
			else:
				print('pasv_addr not set')

			resp = self._recv() # 500 or 150
			self._print(resp)	

			if not self._pasv_addr:
				return

			resp_res = PARSE_RESP.match(resp)
			if resp_res is None:
				print('Error response format!', file=sys.stderr)
				return
			if resp_res['code'] != '150':
				return

			filesize = -1

			if parse_res['cmd'] == 'LIST':
				filename = 'list.txt'
			elif parse_res['cmd'] == 'RETR':
				if parse_res['args'] is None:
					print('Wrong command format!', file=sys.stderr)
					return

				retr_res = RETR_FILENAME.search(parse_res['args'])
				if retr_res is None:
					print('Wrong command format!', file=sys.stderr)
					return

				filename = retr_res.group(0)

				filesize = int(FILE_SIZE.search(resp_res['info'])['size'])

			else:
				filename = 'untitled.out'

			resp = self._recv() #226
			resp_res = PARSE_RESP.match(resp)
			if resp_res is None:
				print('Error response format!', file=sys.stderr)
				return
			if resp_res['code'] != '226':
				print(f'Error response code {resp_res["code"]}!', file=sys.stderr)
				return

			self._get_resp(filename, filesize)
			print(f'Saved to file {filename}')

		else:
			resp = self._recv()
			self._print(resp)



def int_or_str(text):
	"""Helper function for argument parsing."""
	try:
		return int(text)
	except ValueError:
		return text


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('dst_ip')
parser.add_argument('dst_port')
parser.add_argument('-r', '--recv-device', type=int_or_str,
					help='recv device (numeric ID or substring)')
parser.add_argument('-t', '--send-device', type=int_or_str,
					help='send device (numeric ID or substring)')


if __name__ == '__main__':

	args = parser.parse_args()

	with FTP((sys.argv[1], int(sys.argv[2])),
				addr=0x77, rx_device=args.recv_device, tx_device=args.send_device,
				ack_timeout=1, max_retries=20, mtu=1500) as ftp:

		while ftp.connected():
			print('> ', end='')
			try:
				cmd = input()
			except EOFError:
				break
			except KeyboardInterrupt:
				break
			except Exception as e:
				print(e)
				break

			if cmd != '':
				ftp.do(cmd)
