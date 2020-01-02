# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-10-09 23:38:13
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-17 20:07:22


import sounddevice as sd
import numpy as np
import time

from constants import *


def encode(data):
    # msg = bytes([int(txt[i*8:i*8+8], 2) for i in range(len(txt) / 8)])
    # return msg
    return data
    # return LUT_45[data]

def modulate(encoded):
    # return LUT_MOD_5[encoded]
    return LUT_MOD[encoded]

def readfile():
    with open('INPUT.txt') as f:
        txt = f.read().strip()
    return txt

if __name__ == '__main__':
    data = readfile()[:NUM_TRANS]
    data = data
    # data = '1101111100111011'

    # length = len(data)
    # data += '0' * (length % 4)

    # print([encode(int(data[i*4:(i+1)*4], 2)) for i in range(len(data) // 4)])

    with open('INPUT.bin', 'rb') as f:
        data = f.read()[:NUM_TRANS]

    modulated = np.concatenate([modulate(encode(d)) for d in data])
    # modulated = np.concatenate([modulate(encode(int(data[i*4:(i+1)*4], 2))) for i in range(len(data) // 4)])
    print(len(modulated))

    sd.play(np.concatenate((HEADER,GAP,modulated)),blocking=True,samplerate=SAMPLERATE,device=2)
