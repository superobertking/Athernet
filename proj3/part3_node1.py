from aocket import Aocket
from ip import IP_TYPE, ICMP_TYPE

import argparse
import time
from datetime import datetime
import numpy as np


def int_or_str(text):
	"""Helper function for argument parsing."""
	try:
		return int(text)
	except ValueError:
		return text

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-r', '--recv-device', type=int_or_str,
					help='recv device (numeric ID or substring)')
parser.add_argument('-t', '--send-device', type=int_or_str,
					help='send device (numeric ID or substring)')
args = parser.parse_args()


if __name__ == '__main__':
	with Aocket(addr=0x77, rx_device=args.recv_device, tx_device=args.send_device,
				ack_timeout=0.2, max_retries=20, mtu=1500) as aocket:

		# dst = '119.75.217.26'
		dst = '10.19.72.1'
		for i in range(1, 11):
			succeed, duration, payload = aocket.ping('192.168.1.2', dst, np.frombuffer(b'hello, world\n\000\000\000', dtype=np.uint8))
			if succeed:
				print(f'Ping {dst} request sequence {i} received reply after {duration} with payload {payload.tobytes()}')
			else:
				print(f'Ping {dst} request sequence {i} timeout after {duration}')
			time.sleep(1)
