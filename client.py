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

current_server_port = int (sys.argv[1])
server_address = ('127.0.0.1', current_server_port) 
multicast_group = ('224.1.1.1', 12000)
rec_msg_buffer_size = 2048
my_joiningdate = None

def getCurrentDateTime():
	return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#also listen to multicast socket
multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
multicast_socket.bind(multicast_group)
group = socket.inet_aton(multicast_group[0])
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

#open socket on same IP (localhost) and using same port
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#TTL (time-to-live) value shows how many networks will get the sent packet. TTL value = [1...255] and is packet in a sigle byte.
# Set the TTL for messages to 1 so they do not go past the local network segment.
ttl = struct.pack('b', 1)
client_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
#send connection message to the server
client_socket.sendto(MessageUtil.constructMessage(None, SenderType.CLIENT, -1, MessageType.JOINROOM, 'new_client', str(getCurrentDateTime())), server_address)

sys.stdout.write('[Me:] '); sys.stdout.flush()

while True:
	#consider as sockets the std input file and the client socket created
	client_socket_list = [sys.stdin, client_socket, multicast_socket]

	#each iteration check if the 2 sockets ready for reading (having data into them)
	read_sockets, write_sockets, error_sockets = select.select(client_socket_list, [], [])

	#if current socket is readable, then wait for msg from server
	for socket in read_sockets:
		#if client socket has data =>server sent a message
		if socket == sys.stdin:
			#send message to server. Even if #q is typed, firstly inform the server
			try:
				client_message = sys.stdin.readline()
				if client_message:
					if (client_message.strip() == MessageContent.QUIT):
						client_socket.sendto(MessageUtil.constructMessage(None, SenderType.CLIENT, -1, MessageType.LEFTROOM, client_message, str(getCurrentDateTime())), server_address)
						client_socket.close()
						sys.exit(0)
					else:
						print server_address
						client_socket.sendto(MessageUtil.constructMessage(None, SenderType.CLIENT, -1, MessageType.NORMALCHAT, client_message, str(getCurrentDateTime())), server_address)
						sys.stdout.write('[Me:] ')
						sys.stdout.flush()
			except:
				print ('The message could not be sent. The socket will close. Type <~q> to exit the application')
				client_socket.sendto(MessageUtil.constructMessage(None, SenderType.CLIENT, -1, MessageType.LEFTROOM, client_message, str(getCurrentDateTime())), server_address)
				#client_socket.sendto(MessageUtil.constructMessage(None, SenderType.CLIENT, -1, MessageType.CLIENTREJOIN, client_message, str(getCurrentDateTime())), multicast_group)
				client_socket.close()
		else:
			server_message, server_address = socket.recvfrom(rec_msg_buffer_size)
			#extract information from the message received from server
			sender_id, sender_type, message_id, message_type, message_content, message_datetime = MessageUtil.extractMessage(server_message)
			
			if socket == client_socket:
				if not server_message:
					print ('disconnected from server')
				else:
					sys.stdout.write('\n')
					if (sender_type == SenderType.SERVER):
						if (message_type == MessageType.JOINROOM or message_type == MessageType.LEFTROOM or message_type == MessageType.SERVERBUSY):
							sys.stdout.write("%s \n"%(message_content))
						
						if (message_type == MessageType.ACKNOWLEDGEFROMSERVER):
							my_joiningdate = MessageUtil.convertStringToDateTime(message_content)
							sys.stdout.write("Joined the chat room at %s \n"%(message_content))
					else:
						if (MessageUtil.convertStringToDateTime(message_datetime) >= my_joiningdate):
							sys.stdout.write("[%s at %s] %s"%(sender_id, message_datetime, message_content))
					sys.stdout.write('[Me:] '); sys.stdout.flush()
	
			if socket == multicast_socket and server_message:
				if(sender_type == SenderType.SERVER):
					if(message_type == MessageType.ANNOUNCEMENTSLAVEDOWN):
						arr_contents = message_content.split("#")
						temp_current_server_port = int(arr_contents[0])
						new_server_port = int(arr_contents[1])
						
						if (temp_current_server_port == current_server_port):
							server_address[1] = new_server_port
					
					
					
