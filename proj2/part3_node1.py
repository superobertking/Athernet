# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-17 19:07:52
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-18 05:47:08


from mac import MAC

import argparse
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
	mac = MAC(rx_device=args.recv_device, tx_device=args.send_device,
			  ack_timeout=0.5, max_retries=20, mtu=100)
	mac.start()

	with open('INPUT.bin', 'rb') as f:
		raw_data = f.read()
	mac.send(np.frombuffer(raw_data, dtype=np.uint8))

	packet = mac.recv()
	with open('OUTPUT2to1.bin', 'wb') as f:
		f.write(packet.tobytes())

	mac.shutdown()
