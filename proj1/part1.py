# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-10-14 21:16:02
# @Last Modified by:   robertking
# @Last Modified time: 2018-10-14 21:26:27


import sys
import numpy as np
import sounddevice as sd

fs = 44100

def p1():
	duration = 10.5

	myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
	sd.wait()

	sd.play(myrecording, blocking=True)

def p2():
	myarray = np.sin(2 * np.pi * 500 * np.linspace(0, 10, 44100 * 10))
	myrecording = sd.playrec(myarray, fs, channels=2, blocking=True)

	sd.play(myrecording, blocking=True)

if __name__ == '__main__':
	if len(sys.argv) == 1:
		p1()
	else:
		p2()
