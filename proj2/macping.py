# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-18 18:39:54
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-18 20:33:38


from mac import MAC

import argparse
import numpy as np
import time
import queue


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
parser.add_argument('-s', '--src-addr', type=int_or_str,
					help='source addr (numeric ID or substring)')
parser.add_argument('-d', '--dst-addr', type=int_or_str,
					help='destination device (numeric ID or substring)')
parser.add_argument('-m', '--mtu', type=int_or_str,
					help='mtu (numeric ID or substring)', default=512)
parser.add_argument('-x', '--sleep', type=int_or_str,
					help='sleep (numeric ID or substring)', default=512)
args = parser.parse_args()

if __name__ == '__main__':
	with MAC(addr=args.src_addr, rx_device=args.recv_device, tx_device=args.send_device,
			  ack_timeout=0.5, max_retries=20, mtu=args.mtu) as mac:
		while True:
			time.sleep(args.sleep)
			try:
				timediff = mac.ping(args.dst_addr, timeout=2)
				print('macping: RTT {}'.format(timediff.total_seconds()))
			except queue.Empty:
				print('macperf: TIMEOUT')
