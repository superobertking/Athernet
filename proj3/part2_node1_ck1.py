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
				ack_timeout=0.2, max_retries=100, mtu=1500) as aocket:

		with open('INPUT.txt', 'rb') as f:
			ctt = f.readlines()

		for l in ctt:
			aocket.send(IP_TYPE.UDP, ('192.168.1.2', 16384), ('10.20.197.191', 10000), np.frombuffer(l, dtype=np.uint8))
