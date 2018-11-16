# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-10-14 20:57:47
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-16 10:45:55


import numpy as np


with open('INPUT.txt') as f:
    t1 = np.array([int(x) for x in f.read().strip()])

with open('OUTPUT.txt') as f:
    t2 = np.array([int(x) for x in f.read().strip()])


maxi = 0
off = []

print(len(t1), len(t2))

for i in range(len(t2) - 1):
    if len(t2) - i > len(t1):
        tt = t2[i:i + len(t1)]
    else:
        tt = np.concatenate((t2[i:], np.zeros(len(t1) - (len(t2) - i), dtype=np.int64)))
    if np.sum(t1 == tt) > maxi:
        maxi = np.sum(t1 == tt)
        off = [i]
    elif np.sum(t1 == tt) == maxi:
        off.append(i)

print(str(maxi / 100) + '%', off)
