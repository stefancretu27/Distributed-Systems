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
#create server
this_server = UDPServerModel('127.0.0.1', int (sys.argv[1]))
#open server socket
this_server.openSocket()
print('Server is starting up on %s port %s' % (this_server.ip, this_server.port))

#store all connected clients in a global list	
list_of_clients = list()

#list of clients related operations
#for various reasons a client will disconnect => update the list of clients
def disconnectClient(client_list, this_client):
	if client_list:
		return [client for client in client_list if client != this_client]

#display the port and ip of all clients
def showConnectedClients():
	if list_of_clients:
		for client in list_of_clients:
			print (client.address)
	else:
		print ('No clients are currently connected to this server:', this_server.ip)

#search if a client is connected	
def findClientInList(this_client):
	for client in list_of_clients:
		if this_client == client:
			return client

#send a message to all connected clients but to the one that sent it
def multicastMessage(this_client, message_type):
	#this_server.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
	multicast_sendertype = SenderType.CLIENT
	multicast_senderid = "%s:%s"%(this_client.address[0], this_client.address[1])
	multicast_message = this_client.message
	if (message_type == MessageType.LEFTROOM or message_type == MessageType.JOINROOM):
		if (message_type == MessageType.JOINROOM):
			multicast_message = '************************ client %s:%s joined the room ********************************' %(this_client.address[0],this_client.address[1])
		else:
			multicast_message = '************************ client %s:%s left the room ****************************' %(this_client.address[0],this_client.address[1])
		multicast_sendertype = SenderType.SERVER
		multicast_senderid = "%s:%s"%(this_server.ip, this_server.port)

	for client in list_of_clients:
		if client != this_client:
			# this_server.socket.sendto(this_client.message, client.address)
			this_server.socket.sendto(MessageUtil.constructMessage(multicast_senderid, multicast_sendertype, message_type, multicast_message), client.address)

while True:
	#Each time a message is received, create a temporary client with the received attributes(message + address)
	#Recvfrom takes as input message buffer size = the maximum length for the received message
	#it outputs a pair: first is the data = the message; the second is the client's socket address
	temp_client = ClientModel(None, None)
	# temp_client.message, temp_client.address = this_server.socket.recvfrom(message_buffer_size)
	temporary_message, temp_client.address= this_server.socket.recvfrom(message_buffer_size)
	sender_id, sender_type, message_type, message_content = MessageUtil.extractMessage(temporary_message)

	temp_client.message = message_content
	client_ip, client_port = temp_client.address

	#new client has requested to join the conversation
	if (sender_type == SenderType.CLIENT):
		if (message_type == MessageType.JOINROOM):
			temp_client.message = ''
			list_of_clients.append(temp_client)

			#show the entire list of available connections
			print ('A new client has joined. The current logged in clients are:')
			for client in list_of_clients:
				print (client.address)

			#send message to the other connected clients
			multicastMessage(temp_client, MessageType.JOINROOM)
		else:
			#find this client's attributes in list of connected clients
			existing_client = findClientInList(temp_client)
			#update message for the existing_client instance
			if existing_client is not None:
				existing_client.setMessage(temp_client.message)

				#if the client exited, the client application sends a 'quit' message. Remove this client from the client list
				if (message_type == MessageType.LEFTROOM):
					multicastMessage(existing_client, MessageType.LEFTROOM)
					list_of_clients = disconnectClient(list_of_clients, existing_client)
					print ('Client', existing_client.address ,'has left. The current logged in clients are:')
					showConnectedClients()
				else:
					#overwrite his message in list, as only the last message matters.
					for client in list_of_clients:
						if client == existing_client:
							client.setMessage(existing_client.message)
					#send message to the other connected clients
					multicastMessage(existing_client, MessageType.NORMALCHAT)
