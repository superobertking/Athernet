# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-10-09 22:39:27
# @Last Modified by:   robertking
# @Last Modified time: 2018-10-09 22:56:17


import numpy as np
import sounddevice as sd
import time

fs = 44100

d = 100
t = np.linspace(0,d,fs*d)
ft = np.sin(2*np.pi*1000*t) + np.sin(2*np.pi*10000*t)

sd.play(ft, fs)
time.sleep(100)
