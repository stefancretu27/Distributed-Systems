#used for reading process arguments
import sys

#Socket allows for inter-process communication regardless they run on the same machine or on different machines. 
# It uses UNIX file descriptors, as I/O operations are done by opening, reading from/ writing to and close file which has an unique ID (file descriptor).
#import socket package
import socket
import time
#import classes
from ClientModel import ClientModel
from UDPServerModel import UDPServerModel
from MessageUtil import MessageUtil
from Enum import MessageType,SenderType

#set message buffer size
message_buffer_size = 2048
#create server instance to handle communication with clients
server_client = UDPServerModel('127.0.0.1', int (sys.argv[1]))
#open server socket
server_client.openSocket()

#create server instance to handle communication with other servers
server_server = UDPServerModel('127.0.0.1', int (sys.argv[2]))
#open server socket
server_server.openSocket()

#store all connected clients in a global list	
list_of_clients = list()

#list of clients related operations
#for various reasons a client will disconnect => update the list of clients
def disconnectClient(client_list, this_client):
	if client_list:
		return [client for client in client_list if client != this_client]
	else:
		return []

#display the port and ip of all clients
def showConnectedClients():
	if list_of_clients:
		for client in list_of_clients:
			print (client.address)
	else:
		print ('No clients are currently connected to this server:', server_client.ip)

#search if a client is connected	
def isClientInList(this_client):
	for client in list_of_clients:
		if client == this_client:			
			return True
	return False
			
#send a message to all connected clients but to the one that sent it
def multicastMessagetoClients(this_client, message_type):
	#set message's parameters
	#message received from a clien and multicasted to the other clients
	multicast_sendertype = SenderType.CLIENT
	#the sender client is identified based on its ip and port, taken from address
	multicast_senderid = "%s:%s"%(this_client.address[0], this_client.address[1])
	#message content is not altered
	multicast_message = this_client.message
	#if a client joins or leaves
	if (message_type == MessageType.LEFTROOM or message_type == MessageType.JOINROOM):
		#create notification
		if (message_type == MessageType.JOINROOM):
			multicast_message = '************************ client %s:%s joined the room ********************************' %(this_client.address[0],this_client.address[1])
		else:
			multicast_message = '************************ client %s:%s left the room ****************************' %(this_client.address[0],this_client.address[1])
		#the server sends notifications to all connected clients
		multicast_sendertype = SenderType.SERVER
		#specify the identity of the server that handles the join/leave operation
		multicast_senderid = "%s:%s"%(server_client.ip, server_client.port)
	#multicast the message
	for client in list_of_clients:
		if client != this_client:
			server_client.socket.sendto(this_client.message, client.address)	

while True:
	#communicate with clients and servers using different sockets
	server_socket_list = [server_client.socket, server_server.socket]

	#each iteration check if this server instance received data from a client or from a server
	read_sockets, write_sockets, error_sockets = [server_socket_list, [], []]

	for socket in server_socket_list:
		# if there is a message received from a client
		if socket == server_client.socket:
			#Each time a message is received, create a temporary client with the received attributes(message + address)
			#Recvfrom takes as input message buffer size = the maximum length for the received message
			#it outputs a pair: first is the data = the message; the second is the client's socket address
			temp_client = ClientModel(None, None)
			temp_client.message, temp_client.address = server_client.socket.recvfrom(message_buffer_size)
			#extract data from packet
			sender_id, sender_type, message_type, message_content = MessageUtil.extractMessage(temp_client.message)

			#new a client has requested to join the conversation
			if (sender_type == SenderType.CLIENT):
				if (message_type == MessageType.JOINROOM):
					#set his message to empty string and append its attributes to list of clients
					temp_client.message = ''
					list_of_clients.append(temp_client)

					#show the entire list of available connections
					print ('A new client has joined. The current logged in clients are:')
					for client in list_of_clients:
						print (client.address)

					#send message to the other connected clients
					multicastMessagetoClients(temp_client, MessageType.JOINROOM)
				else:
					#if the client is in list, check the message type
					if isClientInList(temp_client):
						# if he exited, the client application sends a 'quit' message. 
						if (message_type == MessageType.LEFTROOM):
							#notify the other clients
							multicastMessagetoClients(existing_client, MessageType.LEFTROOM)
							#Remove this client from the list of clients
							list_of_clients = disconnectClient(list_of_clients, temp_client)
							#show results on server side
							print ('Client', temp_client.address ,'has left. The current logged in clients are:')
							showConnectedClients()
						else:
							#update his message in list, as only the last message matters. Also, the message was previously updated in the local variable existing_client
							for client in list_of_clients:
								if client == temp_client:
									client.setMessage(temp_client.message)
							#send message to the other connected clients
							multicastMessagetoClients(temp_client, MessageType.NORMALCHAT)
			#handle server to server communication
			#if socket == server_server.socket:
				#store data from the received message in a local variable of type UDPServerModel
				#temp_server = UDPServerModel(None, None)
				#temp_server.message, temp_address = server_server.socket.recvfrom(message_buffer_size)

				#temp_server.ip, temp_server.port = temp_address
				#message_to_server = 'ack'
				#server_server.socket.sendto(message_from_client, (temp_server.ip, temp_server.port))
				
