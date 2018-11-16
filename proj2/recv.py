# -*- coding: utf-8 -*-

from constants import *

import time
import argparse
import math
import queue

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
parser.add_argument('-i', '--input', type=str, default=None,
					help='input filename, default sound device')
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

def handle_buffer(sig_recv):
	# synchronize
	sig_buffer = np.array([])
	while sig_buffer.size<HEADER_FRAMECNT:
		sig_buffer = np.concatenate((sig_buffer,sig_recv.get()[1]))
	cursor = HEADER_FRAMECNT
	print("read enough buffer, start sync")
	
	time_deatch = 0
	max_rate = 0
	cursor_align = None
	found_align = False
	while not found_align:
		# the query will be blocked
		sig = sig_recv.get()[1]
		sig_buffer = np.concatenate((sig_buffer,sig))
		for i in range(cursor,sig_buffer.size):
			coupling = np.sum(sig_buffer[i-HEADER_FRAMECNT:i]*HEADER)
			power = np.sum(np.square(sig_buffer[i-HEADER_FRAMECNT:i]))
			rate = coupling*coupling/power
			if power>1 and rate>60:
				time_deatch = 0
				if rate>max_rate:
					print("big rate",rate)
					max_rate = rate
					cursor_align = i
			else:
				if cursor_align is None:
					continue
				time_deatch += 1
				if time_deatch>=2000:
					found_align = True
					break
				
		# print("%8.2f %8.2f %8.2f" % (coupling,power,max_coupling))
		if cursor_align is None and sig_buffer.size>10*HEADER_FRAMECNT and False:
			sig_buffer = sig_buffer[-HEADER_FRAMECNT:]
		cursor = sig_buffer.size
	print("head locked, skipping gap")

	# last_get = np.arange(2205)
	# skip the gap
	while sig_buffer.size-cursor_align<GAP_FRAMECNT:
		print("gap stage:",sig_buffer.size,cursor_align,GAP_FRAMECNT)
		sig = sig_recv.get()[1]
		sig_buffer = np.concatenate((sig_buffer,sig))
		# print(np.all(this_get == last_get))
		# last_get = this_get
	sig_buffer = sig_buffer[cursor_align+GAP_FRAMECNT:]
	cursor = 0
	print("gap skipped, start decoding")

	cnt_decode = 0

	stat = []
	res = []
	# decode
	while cnt_decode<11000:
		while sig_buffer.size<cursor+FRAMECNT:
			sig = sig_recv.get()[1]
			sig_buffer = np.concatenate((sig_buffer,sig))
		for i in range(cursor,sig_buffer.size-FRAMECNT+1,FRAMECNT):
		#	print("size of sig_buffer: ", sig_buffer.size)
		#	print("size of SIG_HI: ", SIG_HI.size)
			sig_shift = sig_buffer[i:i+FRAMECNT]*SIG_HI
			# print(np.max(sig_shift), np.min(sig_shift))
			sigsum = np.sum(sig_shift)
			# print("* %12.6f" % (sigsum/FRAMECNT))
			if len(stat) < 100:
				stat.append(sigsum)
				if len(stat) == 100:
					# stat = sorted(stat)
					div = sum(stat) / 100 * 0.618
					# div = (stat[0] + stat[-1]) / 2
			else:
				cnt_decode += 1
				res.append('1' if sigsum > div else '0')
		# print("LOOP",i,cursor)
		cursor = i+FRAMECNT
		if sig_buffer.size>10*FRAMECNT and False:
			cursor = cursor-(sig_buffer.size-FRAMECNT)
			sig_buffer = sig_buffer[-FRAMECNT:]

	with open('OUTPUT.txt', 'w') as fout:
		fout.write(''.join(res[500:10500]))


def read_device():
	try:
		with sd.InputStream(device=args.device, channels=2, callback=receive_signal,
							blocksize=int(samplerate * args.block_duration / 1000),
							samplerate=samplerate):
			handle_buffer(sig_recv)
	except KeyboardInterrupt:
		# parser.exit('Interrupted by user')
		print("Interrupted by user")
	except Exception as e:
		# parser.exit(type(e).__name__ + ': ' + str(e))
		print(type(e).__name__ + ': ' + str(e))


def read_file(filename):
	filedata = np.load(filename)
	q = queue.Queue()
	q.put((None,filedata,None))
	q.put((None,filedata,None))
	handle_buffer(q)


if args.list_devices:
	print(sd.query_devices())
	parser.exit(0)

filename = args.input
if filename is None:
	read_device()
else:
	read_file(filename)
print("Done.")