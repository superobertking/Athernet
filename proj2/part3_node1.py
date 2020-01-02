# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-17 19:07:52
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-28 00:50:56


from mac import MAC

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
	with MAC(addr=0xee, rx_device=args.recv_device, tx_device=args.send_device,
			  ack_timeout=1, max_retries=100, mtu=50) as mac:

		start_time = datetime.now()

		with open('INPUT.bin', 'rb') as f:
			raw_data = f.read()
		mac.send(0x77, np.frombuffer(raw_data, dtype=np.uint8))

		packet = mac.recv()
		with open('OUTPUT2to1.bin', 'wb') as f:
			f.write(packet.tobytes())

		end_time = datetime.now()

		try:
			time.sleep(1000)
		except KeyboardInterrupt:
			pass

		print('Time consumed:', end_time - start_time)
