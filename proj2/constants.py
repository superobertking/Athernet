# -*- coding: utf-8 -*-

import numpy as np
import sounddevice as sd
from scipy import integrate

LUT_45 = {
    0b0000: 0b11110,
    0b0001: 0b01001,
    0b0010: 0b10100,
    0b0011: 0b10101,
    0b0100: 0b01010,
    0b0101: 0b01011,
    0b0110: 0b01110,
    0b0111: 0b01111,
    0b1000: 0b10010,
    0b1001: 0b10011,
    0b1010: 0b10110,
    0b1011: 0b10111,
    0b1100: 0b11010,
    0b1101: 0b11011,
    0b1110: 0b11100,
    0b1111: 0b11101,
}

LUT_54 = {LUT_45[k]: k for k in LUT_45}

SAMPLERATE = 48000

FREQ_HI = 8000
FREQ_LO = 4000

# FRAMECNT = 24000
# SAMPLESIZE = FRAMECNT
# DURATION = 0.5
FRAMECNT = 3
SAMPLESIZE = FRAMECNT
DURATION = 0.0000625
# FRAMECNT = 48
# SAMPLESIZE = FRAMECNT
# DURATION = 0.001

SIG_HI = np.sin(2 * np.pi * FREQ_HI * np.linspace(0, DURATION, FRAMECNT, endpoint=False))
# SIG_LO = np.sin(2 * np.pi * FREQ_LO * np.linspace(0, DURATION, FRAMECNT, endpoint=False))
SIG_LO = -1 * np.sin(2 * np.pi * FREQ_HI * np.linspace(0, DURATION, FRAMECNT, endpoint=False))

LUT_SIG = {1: SIG_HI, 0: SIG_LO}
LUT_MOD_4 = {k: np.concatenate([LUT_SIG[(k >> (3-i)) & 1] for i in range(4)]) for k in LUT_45}
LUT_MOD_5 = {k: np.concatenate([LUT_SIG[(k >> (4-i)) & 1] for i in range(5)]) for k in LUT_54}
LUT_MOD = {k: np.concatenate([LUT_SIG[(k >> (7-i)) & 1] for i in range(8)]) for k in range(256)}

header_duration = 0.004
HEADER_FRAMECNT = int(header_duration*SAMPLERATE)//2*2
PREAMBLE_SAMPLESIZE = HEADER_FRAMECNT
header_time = np.linspace(0,header_duration,HEADER_FRAMECNT)
header_frequency = np.concatenate((np.linspace(FREQ_LO,FREQ_HI,HEADER_FRAMECNT/2),np.linspace(FREQ_HI,FREQ_LO,HEADER_FRAMECNT/2)))
HEADER = np.sin(2*np.pi*integrate.cumtrapz(header_frequency,header_time,initial=0))
PREAMBLE = HEADER
# header_frequency = np.arange(FREQ_LO,FREQ_HI,(FREQ_HI-FREQ_LO)/(SAMPLERATE*header_duration))
# HEADER = np.sin(2*np.pi*header_frequency)

GAP_FRAMECNT = 0
GAP = np.sin(2*np.pi*(FREQ_LO*2)*np.linspace(0,GAP_FRAMECNT/SAMPLERATE,GAP_FRAMECNT))

NUM_TRANS = 16
NUM_TRANS_45 = NUM_TRANS // 4 * 5

# import matplotlib.pyplot as plt
# plt.plot(header_time,HEADER)
# plt.show()