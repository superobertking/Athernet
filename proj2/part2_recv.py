# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-17 19:07:52
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-18 18:06:46


import argparse
import numpy as np

from mac import MAC


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
	mac = MAC(addr=0x77, rx_device=args.recv_device, tx_device=args.send_device)
	mac.start()

	packet = mac.recv()

	with open('OUTPUT.bin', 'wb') as f:
		f.write(packet.tobytes())

	mac.shutdown()
