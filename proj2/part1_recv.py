# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-17 19:07:52
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-17 20:09:13


from receiver import Receiver
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
	receiver = Receiver(device=args.device)
	receiver.start()

	print('receiving...')
	data = receiver.recv()
	print(len(data))
	print('data received')

	receiver.shutdown()

	with open('OUTPUT.bin', 'wb') as f:
		f.write(data.tobytes())
