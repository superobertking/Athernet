# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-17 18:58:36
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-17 20:01:03


from constants import NUM_TRANS

from sender import Sender
import argparse
import numpy as np


def int_or_str(text):
	"""Helper function for argument parsing."""
	try:
		return int(text)
	except ValueError:
		return text

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-d', '--device', type=int_or_str,
					help='input device (numeric ID or substring)')
args = parser.parse_args()

if __name__ == '__main__':
	with open('INPUT.bin', 'rb') as f:
		raw_data = f.read()[:2]

	sender = Sender(device=args.device)
	sender.start()

	print('sending...')
	sender.send(np.frombuffer(raw_data, dtype=np.uint8))
	print('data sent')

	sender.shutdown()
