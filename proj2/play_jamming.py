# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-18 03:30:07
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-18 03:31:28


from constants import SAMPLERATE

import numpy as np

import soundfile as sf
import sounddevice as sd


data, fs = sf.read('Jamming.wav', dtype=np.float32)

sd.play(data, fs, blocking=True, device=(1, 2))
