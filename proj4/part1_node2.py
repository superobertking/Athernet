from gateway import Gateway
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


if __name__ == '__main__':
	args = parser.parse_args()
	with Gateway(addr=0xee, rx_device=args.recv_device, tx_device=args.send_device,
				ack_timeout=1, max_retries=20, mtu=1500) as aocket:
		try:
			time.sleep(10000)
		except KeyboardInterrupt:
			pass
