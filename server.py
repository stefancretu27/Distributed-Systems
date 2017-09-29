#used for reading process arguments
import sys

#Socket allows for inter-process communication regardless they run on the same machine or on different machines. 
# It uses UNIX file descriptors, as I/O operations are done by opening, reading from/ writing to and close file which has an unique ID (file descriptor).
#import socket package
import socket
import unicodedata
import datetime
#import classes
from UDPServerModel import UDPServerModel
from ClientModel import ClientModel
from MessageUtil import MessageUtil
from Enum import MessageType,SenderType
from MessageHistoryModel import MessageHistoryModel

def getCurrentServerDateTime():
	return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#set message buffer size
message_buffer_size = 2048
default_server_port = 5005

#set list of message history
lst_messagehistory = []

#create server instance to handle communication with clients
this_server = UDPServerModel('127.0.0.1', int (sys.argv[1]), int (sys.argv[2]))
#open server socket
this_server.openSocket()

#inform the admin that this server is up
print('Server is starting up on %s port %s' % (this_server.ip, this_server.port))
#if not default server, inform the default server about its existence
if this_server.default == 0:
	#create a server instance for the default one
	default_server = UDPServerModel('127.0.0.1', default_server_port, True)
	message_datetime = getCurrentServerDateTime()

	#send message with this server's id, specifying that comes from a server entity, that the server is up and giving the port as message
	this_server.socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.SERVERUP, MessageType.BLANK, message_datetime), default_server.getAddress())

	#append default server to server list as it shall be the 1st
	this_server.list_of_servers.append(default_server)
	#inform the admin which is the default server
	print('The default server runs on %s port %s' % (default_server.ip, default_server.port))
else:
	#append default server to server list as it shall be the 1st
	this_server.list_of_servers.append(this_server)
	#inform the admin that this is the default server
	print('This is the default server')
			

while True:
#Recvfrom takes as input message buffer size = the maximum length for the received message
#it outputs a pair: first is the data = the message; the second is the socket's address
	#read data from socket. At this moment is not known whether data belongs to a client or to a server
	received_packet, received_address = this_server.socket.recvfrom(message_buffer_size)
	serverdatetime_received_packet = getCurrentServerDateTime()
	#extract data from packet
	sender_id, sender_type, message_type, message_content, message_datetime = MessageUtil.extractMessage(received_packet)

#handle communication with the clients
	if (sender_type == SenderType.CLIENT):
	#Each time a message is received from a client, create a temporary client with the received attributes(message + address)
		temp_client = ClientModel(message_content, received_address)

	#if a new client has joined the conversation
		if (message_type == MessageType.JOINROOM):
		#append its attributes to list of clients
			#temp_client.message = ''

		#record joining datetime
			temp_client.setJoiningDateTime(serverdatetime_received_packet)

		#append the new client to the list
			this_server.list_of_clients.append(temp_client)

		#show the entire list of available connections
			print ('A new client has joined. The current logged in clients are:')
			for client in this_server.list_of_clients:
				print (client.address)

		#send message to the other connected clients
			this_server.multicastMessagetoClients(temp_client, MessageType.JOINROOM, serverdatetime_received_packet)

		#send message to the other server instances to inform them that a new client has connected as they need to update their client group view
			this_server.multicastMessageToServers(MessageType.JOINROOM, received_address, serverdatetime_received_packet)

		else:
		#if the client is in list, check the message type
			if this_server.isClientInList(temp_client):
			# if he exited, the client application sends a 'quit' message. 
				if (message_type == MessageType.LEFTROOM):
				#record leving datetime
					temp_client.setLeavingDateTime(serverdatetime_received_packet)

				#notify the other clients
					this_server.multicastMessagetoClients(temp_client, MessageType.LEFTROOM, serverdatetime_received_packet)

				#send message to the other server instances to inform them that a new client has left as they need to update their client group view
					this_server.multicastMessageToServers(MessageType.LEFTROOM, received_address, serverdatetime_received_packet)


				#Remove this client from the list of clients
					this_server.list_of_clients = this_server.disconnectClient(temp_client)
						
				#show results on server side
					print ('Client', temp_client.address ,'has left. The current logged in clients are:')
					this_server.showConnectedClients()
				else:
				#append to message to the message history list
					lst_messagehistory.append(MessageHistoryModel(message_content,serverdatetime_received_packet,temp_client))

				#record message datetime
					temp_client.setMessageDateTime(serverdatetime_received_packet)

				#update his message in list, as only the last message matters. Also, the message was previously updated in the local variable existing_client
					for client in this_server.list_of_clients:
						if client == temp_client:
							client.setMessage(temp_client.message)

				#send message to the other connected clients
					this_server.multicastMessagetoClients(temp_client, MessageType.NORMALCHAT, serverdatetime_received_packet)

				#print message history
					print("------------------- History of the message---------------------------")
					for msg in lst_messagehistory:
						print(msg.message, msg.messagedatetime, msg.ClientModel.address)

#handle communication with other servers
	if (sender_type == SenderType.SERVER):
	#if a server sent a message, create a server instance considering the receieved address (ip + port)
		temp_server = UDPServerModel(received_address[0], received_address[1], 0)
		serverdatetime_received_acknowledgement = getCurrentServerDateTime()

	#if it is a new server
		if(message_type == MessageType.SERVERUP):
		#the default server informs the other servers that a new server is up
			if this_server.default == 1:
				#append it the way it is to the list of servers, as it is a non default server
				this_server.list_of_servers.append(temp_server)
				print ('A new server is up. It runs on the address:', temp_server.getAddress())

				this_server.multicastMessageToServers(MessageType.SERVERUP, this_server.getConnectedServersAddresses(), serverdatetime_received_acknowledgement)
			else:
				# a non-default server receives notifications from defaut server, thus that server can't be appended again. 
				#The port of the new server is sent as message content
				for address in message_content:
					#get rid of unicode
					address[0] = unicodedata.normalize('NFKD', address[0]).encode('ascii','ignore')
					#create local server instance 
					local_server = UDPServerModel(address[0], address[1], 0)
					#if the server is not in the list, add it
					if local_server not in this_server.list_of_servers:
						this_server.list_of_servers.append(local_server)
		#inform the admin about the current connected servers
			print ('The current running servers are:')
			this_server.showConnectedServers()

	#if a new client has connected to another server instance, update local list_of_clients		
		if(message_type == MessageType.JOINROOM):
			#the message content is the new client's address = ip+port (received as list, not as tuple)
			message_content[0] = unicodedata.normalize('NFKD', message_content[0]).encode('ascii','ignore')
			new_client = ClientModel('', (message_content[0], message_content[1]))
			if new_client not in this_server.list_of_clients:
				this_server.list_of_clients.append(new_client)
				sender_id[0] = unicodedata.normalize('NFKD', sender_id[0]).encode('ascii','ignore')
				print ('A new client has joined on server:', sender_id)
				print ('The current connected clients in the system are:')
				this_server.showConnectedClients()

		if(message_type == MessageType.LEFTROOM):
			#the message content is the new client's address = ip+port (received as list, not as tuple)
			message_content[0] = unicodedata.normalize('NFKD', message_content[0]).encode('ascii','ignore')
			old_client = ClientModel('', (message_content[0], message_content[1]))
			#Remove this client from the list of clients
			this_server.list_of_clients = this_server.disconnectClient(old_client)
			#show results on server side
			print ('Client', old_client.address ,'has left. The current logged in clients are:')
			this_server.showConnectedClients()

	#if the server stopped running
		if(message_type == MessageType.SERVERDOWN):
		#remove it from the list of servers
			this_server.disconnectServer(temp_server)
		#inform the admin about the current connected servers
			print ('The server:', temp_server.getAdress(), 'is down. The current running servers are:')
			this_server.showConnectedServers()
		

