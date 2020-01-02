import socket
import sys
import time

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (sys.argv[1], 10001)
message = b'This is the message.  It will be repeated.'

REP_TIMES = 10

sock.bind(('0.0.0.0', 10000))

with open('INPUT.txt', 'rb') as f:
	ctt = f.readlines()

try:
	for l in ctt:
		print('sending', l, 'to', server_address)
		sent = sock.sendto(l, server_address)
		time.sleep(0.3)

finally:
	print('closing socket')
	sock.close()
