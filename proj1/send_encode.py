# -*- coding: utf-8 -*-
# @Author: robertking
# @Date:   2018-10-14 18:01:48
# @Last Modified by:   robertking
# @Last Modified time: 2018-10-14 18:19:59


import reedsolo

rs = reedsolo.RSCodec(10)


def encode(txt):
	msg = bytes([int(txt[i*8:i*8+8], 2) for i in range(len(txt) / 8)])
	return msg

def decode(msg):
	try:
		txt = ''.join([bin(b)[2:] for b in rs.encode(msg)])
	except Exception as e:
		print(e)
	return txt
