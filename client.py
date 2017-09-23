#used for reading process arguments
import sys
#used for inter-process communication
import socket
#
import select
#import classes
from MessageUtil import MessageUtil
from Enum import MessageType,SenderType,MessageContent

UDP_IP = "127.0.0.1"
UDP_PORT = int (sys.argv[1])
rec_msg_buffer_size = 2048

#open socket on same IP (localhost) and using same port
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#send connection message to the server
client_socket.sendto(MessageUtil.constructMessage("",SenderType.CLIENT,MessageType.JOINROOM,""), (UDP_IP, UDP_PORT))

sys.stdout.write('[Me:] '); sys.stdout.flush()

while True:
	#consider as sockets the std input file and the client socket created
	client_socket_list = [sys.stdin, client_socket]

	#each iteration check if the 2 sockets ready for reading (having data into them)
	read_sockets, write_sockets, error_sockets = select.select(client_socket_list, [], [])

	#if current socket is readable, then wait for msg from server
	for socket in read_sockets:
		#if client socket has data =>server sent a message
		if socket == client_socket:
			server_message, server_address = socket.recvfrom(rec_msg_buffer_size)
			#extract information from the message received from server
			sender_id, sender_type, message_type, message_content = MessageUtil.extractMessage(server_message)
			if not server_message:
				print ('disconnected from server')
				#sys.exit()
			else:
				sys.stdout.write('\n')
				if (sender_type == SenderType.SERVER and message_type != MessageContent.QUIT):
					sys.stdout.write("%s \n"%(message_content))
				else:
					sys.stdout.write("[%s] %s"%(sender_id, message_content))
				sys.stdout.write('[Me:] '); sys.stdout.flush()
		#stdin has data => user wrote a message
		else:
			#send message to server. Even if #q is typed, firstly inform the server
			try:
				client_message = sys.stdin.readline()
				if client_message:
					if (client_message.strip() == MessageContent.QUIT):
						client_socket.sendto(MessageUtil.constructMessage("", SenderType.CLIENT, MessageType.LEFTROOM, client_message), (UDP_IP, UDP_PORT))
						client_socket.close()
						sys.exit();
					else:
						client_socket.sendto(MessageUtil.constructMessage("", SenderType.CLIENT, MessageType.NORMALCHAT, client_message), (UDP_IP, UDP_PORT))
						sys.stdout.write('[Me:] ');
						sys.stdout.flush()
			except:
				print ('The message could not be sent. The socket will close. Type <~q> to exit the application')
				client_socket.sendto(MessageUtil.constructMessage("", SenderType.CLIENT, MessageType.LEFTROOM, client_message), (UDP_IP, UDP_PORT))
				client_socket.close()
