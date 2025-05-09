import socket
import sys

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('0.0.0.0', 10000)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

try:
	while True:
		print('\nwaiting to receive message')
		data, address = sock.recvfrom(4096)

		print('received {} bytes from {}'.format(
			len(data), address))
		print(data)
finally:
	print('closing socket')
	sock.close()
