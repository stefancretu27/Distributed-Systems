#used for reading process arguments
import sys
#used for inter-process communication
import socket
import struct
import select
import datetime
#import classes
from MessageUtil import MessageUtil
from Enum import MessageType,SenderType,MessageContent

multicast_group = ('127.0.0.1', int (sys.argv[1])) 
rec_msg_buffer_size = 2048
my_joiningdate = None

def getCurrentDateTime():
	return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#open socket on same IP (localhost) and using same port
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#TTL (time-to-live) value shows how many networks will get the sent packet. TTL value = [1...255] and is packet in a sigle byte.
# Set the TTL for messages to 1 so they do not go past the local network segment.
ttl = struct.pack('b', 1)
client_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
#send connection message to the server
client_socket.sendto(MessageUtil.constructMessage(None, SenderType.CLIENT, -1, MessageType.JOINROOM, 'new_client', str(getCurrentDateTime())), multicast_group)

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
			sender_id, sender_type, message_id, message_type, message_content, message_datetime = MessageUtil.extractMessage(server_message)
			if not server_message:
				print ('disconnected from server')
			else:
				sys.stdout.write('\n')
				if (sender_type == SenderType.SERVER):
					if (message_type == MessageType.JOINROOM or message_type == MessageType.LEFTROOM):
						sys.stdout.write("%s \n"%(message_content))
					else:
						if (message_type == MessageType.ACKNOWLEDGEFROMSERVER):
							my_joiningdate = MessageUtil.convertStringToDateTime(message_content)
							sys.stdout.write("Joined the chat room at %s \n"%(message_content))
				else:
					if (MessageUtil.convertStringToDateTime(message_datetime) >= my_joiningdate):
						sys.stdout.write("[%s at %s] %s"%(sender_id, message_datetime, message_content))
				sys.stdout.write('[Me:] '); sys.stdout.flush()
		#stdin has data => user wrote a message
		else:
			#send message to server. Even if #q is typed, firstly inform the server
			try:
				client_message = sys.stdin.readline()
				if client_message:
					if (client_message.strip() == MessageContent.QUIT):
						client_socket.sendto(MessageUtil.constructMessage(None, SenderType.CLIENT, -1, MessageType.LEFTROOM, client_message, str(getCurrentDateTime())), multicast_group)
						client_socket.close()
						sys.exit(0)
					else:
						client_socket.sendto(MessageUtil.constructMessage(None, SenderType.CLIENT, -1, MessageType.NORMALCHAT, client_message, str(getCurrentDateTime())), multicast_group)
						sys.stdout.write('[Me:] ')
						sys.stdout.flush()
			except:
				print ('The message could not be sent. The socket will close. Type <~q> to exit the application')
				client_socket.sendto(MessageUtil.constructMessage(None, SenderType.CLIENT, -1, MessageType.LEFTROOM, client_message, str(getCurrentDateTime())), multicast_group)
				client_socket.close()
