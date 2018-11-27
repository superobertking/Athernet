# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-18 03:30:07
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-18 03:31:28


from constants import SAMPLERATE

import numpy as np

import soundfile as sf
import sounddevice as sd
import sys

data, fs = sf.read('Jamming.wav', dtype=np.float32)

devices = (1, 2)
if len(sys.argv) == 2:
    devices = int(sys.argv[1])
elif len(sys.argv) > 2:
    devices = tuple(int(x) for x in sys.argv[1:])
print(devices)

sd.play(data, fs, blocking=True, device=devices)
