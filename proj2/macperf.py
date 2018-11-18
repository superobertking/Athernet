# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-18 18:39:54
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-18 22:05:24


from mac import MAC

import argparse
import numpy as np
import datetime
import time


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
args = parser.parse_args()

if __name__ == '__main__':
	with MAC(addr=args.src_addr, rx_device=args.recv_device, tx_device=args.send_device,
			  ack_timeout=0.5, max_retries=20, mtu=args.mtu) as mac:
		sum_mfu = 0
		sum_timediff = datetime.timedelta()
		for i in range(10):
			mfu, timediff = mac.perf(args.dst_addr)
			sum_mfu += mfu
			sum_timediff += timediff
		print('macperf: {} bytes received in {} time, throughput = {} kbps'.format(
			sum_mfu, sum_timediff.total_seconds(), sum_mfu * 8 / 1000 / sum_timediff.total_seconds()))
		time.sleep(10)