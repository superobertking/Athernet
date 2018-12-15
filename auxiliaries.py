# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-11-18 05:21:16
# @Last Modified by:   robertking
# @Last Modified time: 2018-11-18 05:29:11


import numpy as np

def convi2b(x, bts):
	return np.array([(x >> (8*(bts-i-1))) & 0xff for i in range(bts)], dtype=np.uint8)

def convb2i(buf):
	data = 0
	for x in buf:
		data = (data << 8) | x
	return data