#used for reading process arguments
import sys
#used for inter-process communication
import socket
#
import select

UDP_IP = "127.0.0.1"
UDP_PORT = int (sys.argv[1])
rec_msg_buffer_size = 2048

#open socket on same IP (localhost) and using same port
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
connection_message = UDP_IP + UDP_IP
client_socket.sendto(connection_message, (UDP_IP, UDP_PORT))

sys.stdout.write('[Me:] '); sys.stdout.flush()

while True:
	#consider as sockets the std input file and the client socket created
	socket_list = [sys.stdin, client_socket]

	#each iteration check if the 2 sockets ready for reading (having data into them)
	read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])

	#if current socket is readable, then wait for msg from server
	for socket in read_sockets:
		#if client socket has data =>server sent a message
		if socket == client_socket:
			server_message, server_address = socket.recvfrom(rec_msg_buffer_size)
			if not server_message:
				print 'disconnected from server'
				#sys.exit()
			else:
				sys.stdout.write('\n'); sys.stdout.flush()
				sys.stdout.write('[Received message:] '); sys.stdout.flush()
				sys.stdout.write(server_message)
				#sys.stdout.write('\n'); sys.stdout.flush()
				sys.stdout.write('[Me:] '); sys.stdout.flush()
		#stdin has data => user wrote a message
		else:
			#send message to server. Even if #q is typed, firstly inform the server
			try:
				message_from_client = sys.stdin.readline()
				client_socket.sendto(message_from_client, (UDP_IP, UDP_PORT))
				#if the client decided to quit
				if message_from_client.strip() == '~q':
					#client_socket.close()
					sys.exit();
				else:
					sys.stdout.write('[Me:] '); sys.stdout.flush()
			except:
				print 'The message could not be sent. The socket will close. Type <q> to exit the application'
				client_socket.sendto('#q', (UDP_IP, UDP_PORT))
				client_socket.close()
