import socket
import sys
import time

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (sys.argv[1], 10000)
message = b'This is the message.  It will be repeated.'

REP_TIMES = 10

try:
	for i in range(REP_TIMES):
		# Send data
		print('sending {!r}'.format(message))
		sent = sock.sendto(message, server_address)

		# Receive response
		print('waiting to receive')
		data, server = sock.recvfrom(4096)
		print('received {!r}'.format(data))
		if i != REP_TIMES - 1:
			time.sleep(1)

finally:
	print('closing socket')
	sock.close()
