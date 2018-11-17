# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-10-14 20:57:47
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-18 02:21:30


import numpy as np
import sys


with open('OUTPUT.bin', 'rb') as f:
    t1 = np.array([int(x) for x in f.read().strip()])

with open('INPUT.bin', 'rb') as f:
    t2 = np.array([int(x) for x in f.read().strip()])[:len(t1)*2]


maxi = 0
off = []

print(len(t1), len(t2))
assert(len(t1) <= len(t2))

for i in range(len(t2) - len(t1) + 1):
    tt = t2[i:i+len(t1)]
    if np.sum(t1 == tt) > maxi:
        maxi = np.sum(t1 == tt)
        off = [i]
    elif np.sum(t1 == tt) == maxi:
        off.append(i)

print(str(maxi * 100 / len(t1)) + '%', off)

if maxi != len(t1):
    sys.exit(1)
