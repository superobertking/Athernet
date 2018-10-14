# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-10-09 23:38:13
# @Last Modified by:   robertking
# @Last Modified time: 2018-10-14 20:32:13


import sounddevice as sd
import numpy as np
import time

from constants import *


def encode(data):
    return data# LUT_45[data]

def modulate(encoded):
    return LUT_MOD[encoded]

def readfile():
    with open('INPUT.txt') as f:
        txt = f.read().strip()
    return txt


if __name__ == '__main__':
    # data = readfile()
    data = '1010' * 1500

    length = len(data)
    data += '0' * (length % 4)

    # print([encode(int(data[i*4:(i+1)*4], 2)) for i in range(len(data) // 4)])
    modulated = np.concatenate([modulate(encode(int(data[i*4:(i+1)*4], 2))) for i in range(len(data) // 4)])

    sd.play(np.concatenate((HEADER,GAP,modulated)),blocking=True,samplerate=SAMPLERATE)
