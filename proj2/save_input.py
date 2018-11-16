# -*- coding: utf-8 -*-

from constants import *

import time
import argparse
import math
import queue
import matplotlib.pyplot as plt

usage_line = ' press <enter> to quit, +<enter> or -<enter> to change scaling '


def int_or_str(text):
	"""Helper function for argument parsing."""
	try:
		return int(text)
	except ValueError:
		return text


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-l', '--list-devices', action='store_true',
					help='list audio devices and exit')
parser.add_argument('-b', '--block-duration', type=float,
					metavar='DURATION', default=50,
					help='block size (default %(default)s milliseconds)')
parser.add_argument('-d', '--device', type=int_or_str,
					help='input device (numeric ID or substring)')
parser.add_argument('-g', '--gain', type=float, default=10,
					help='initial gain factor (default %(default)s)')
parser.add_argument('-r', '--range', type=float, nargs=2,
					metavar=('LOW', 'HIGH'), default=[100, 2000],
					help='frequency range (default %(default)s Hz)')
args = parser.parse_args()

# samplerate = sd.query_devices(args.device, 'input')['default_samplerate']
samplerate = SAMPLERATE

cnt_callback = 0
sig_max = 0

sig_recv = queue.Queue()

def receive_signal(indata, frames, time, status):
		if status:
			print("Error occurs %r" % status)
		global cnt_callback
		cnt_callback += 1
		# print(cnt_callback)
		# if cnt_callback!=1:
		# 	print("Error cnt_callback = %d" % cnt_callback)
		# 	raise sd.CallbackAbort
		# print(indata[:,0])
		data_reshape = np.array(indata[:,0])
		t = (cnt_callback,data_reshape,id(data_reshape))
		sig_recv.put(t)
		# print(t)
		# cnt_callback -= 1

if args.list_devices:
		print(sd.query_devices())
		parser.exit(0)

try:
	with sd.InputStream(device=args.device, channels=1, callback=receive_signal,
						blocksize=int(samplerate * args.block_duration / 1000),
						samplerate=samplerate):
		
		while True:
			pass

except KeyboardInterrupt:
	sig_buffer = np.array([])
	while not sig_recv.empty():
		sig_buffer = np.concatenate((sig_buffer,sig_recv.get()[1]))
	
	# print(len(sig_buffer))

	# fig = plt.figure()
	# plt.plot(sig_buffer)
	# plt.show()

	np.save("data", sig_buffer)
	print("File saved")

except Exception as e:
	parser.exit(type(e).__name__ + ': ' + str(e))