#used for reading process arguments
import sys
#Socket allows for inter-process communication regardless they run on the same machine or on different machines. 
# It uses UNIX file descriptors, as I/O operations are done by opening, reading from/ writing to and close file which has an unique ID (file descriptor).
#import socket package
import socket
#used for selecting sockets in socket list
import select
#used to parse unicode received IP addresses
import unicodedata
import datetime
import types
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
localhost = '127.0.0.1'

#set list of message history
lst_messagehistory = []

#create server instance, on localhost, to handle client data exchange (with client, but also with servers)
this_server = UDPServerModel(localhost, int (sys.argv[1]))
#open server general socket
this_server.openSocket()
#for this server instance, initialize the discovery socket 
this_server.initializeDiscoverySocket()
#append this_server instance to its own list of servers
this_server.list_of_servers.append(this_server)


#inform the admin that this server is up
print('[Server update] Server is starting up on %s port %s' % (this_server.ip, this_server.port))	

while True:
	socket_list = [this_server.socket, this_server.discovery_socket]

	read_sockets, write_sockets, error_sockets = select.select([], socket_list, [])

	#firstly, announce the others in the multicast group about this instance's existence sending port (argv[1]) as data
	for socket in write_sockets:
		if socket == this_server.discovery_socket:
			message_datetime = getCurrentServerDateTime()
			#send message with this server's id, specifying that comes from a server entity, that the server is up and giving the port as message
			this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.SERVERUP, '', message_datetime), this_server.getDiscoveryAddress())

	#read data received on sockets
	read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])

	for socket in read_sockets:
		if socket == this_server.discovery_socket:
			#recv_data is the port on which the server instance communicates
			#recv_address is the discovery address and is the same for all server instances
			received_packet, received_address = this_server.discovery_socket.recvfrom(1024)
			serverdatetime_received_packet = getCurrentServerDateTime()
			#extract data from packet
			sender_port, sender_type, message_type, message_content, message_datetime = MessageUtil.extractMessage(received_packet)

			#if not own message
			if sender_port != this_server.port:
				#create a temporary server model with the received attributes
				temp_server = UDPServerModel(localhost, sender_port)
				serverdatetime_received_acknowledgement = getCurrentServerDateTime()

				if temp_server not in this_server.list_of_servers:
					this_server.list_of_servers.append(temp_server)
					print ('[Server update] A new server is up. It runs on the address: ' + str(temp_server.getAddress()))

					#send to the newly added server the list of connected clients (if any clients) using the general socket
					if this_server.list_of_clients:
						this_server.unicastMessage(MessageType.JOINROOM, this_server.getConnectedClientsAddresses(), serverdatetime_received_acknowledgement, temp_server.getAddress())

					#inform the admin about the current connected servers (inform that the list of servers has been updated)
					print ('[Server update] The current running servers are:')
					this_server.showConnectedServers()

				
		if socket == this_server.socket:
		##Recvfrom takes as input message buffer size = the maximum length for the received message
		##it outputs a pair: first is the data = the message; the second is the socket's address
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
				#record joining datetime
					temp_client.setJoiningDateTime(serverdatetime_received_packet)
				#append the new client to the list
					this_server.list_of_clients.append(temp_client)

				#show the entire list of available connections
					print ('[Client update] A new client has joined on this server, using the address ' + str(temp_client.address) + '. The current logged in clients are:')
					for client in this_server.list_of_clients:
						print "   ",(client.address)

				#send message to the other server instances to inform them that a new client has connected as they need to update their client group view
					this_server.multicastMessageToServers(MessageType.JOINROOM, received_address, serverdatetime_received_packet)
				#send message to the other connected clients
					this_server.multicastMessagetoClients(temp_client, MessageType.JOINROOM, serverdatetime_received_packet)
			#if a it is an existing client, check the message type
				else:
					if this_server.isClientInList(temp_client):
					# if he exited, the client application sends a 'quit' message. 
						if (message_type == MessageType.LEFTROOM):
						#record leving datetime
							temp_client.setLeavingDateTime(serverdatetime_received_packet)
						#send message to the other server instances to inform them that a new client has left as they need to update their client group view
							this_server.multicastMessageToServers(MessageType.LEFTROOM, received_address, serverdatetime_received_packet)
						#notify the other clients
							this_server.multicastMessagetoClients(temp_client, MessageType.LEFTROOM, serverdatetime_received_packet)
						#Remove this client from the list of clients
							this_server.list_of_clients = this_server.disconnectClient(temp_client)

						#show results on server side
							print ('[Client update] Client ' + str(temp_client.address) + ' has left. The current logged in clients are:')
							this_server.showConnectedClients()
					#if it is an existing client and if it didn't quit
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
				temp_server = UDPServerModel(received_address[0], received_address[1])
				serverdatetime_received_acknowledgement = getCurrentServerDateTime()

			#if a new client has connected to another server instance, update local list_of_clients		
				if(message_type == MessageType.JOINROOM):
					if all(isinstance(elem, list) for elem in message_content):
						for client_address in message_content:
						#the message content is the new client's address = ip+port (received as list, not as tuple)
							client_ip = unicodedata.normalize('NFKD', client_address[0]).encode('ascii','ignore')
							new_client = ClientModel('', (client_ip, client_address[1]))
							if new_client not in this_server.list_of_clients:
								this_server.list_of_clients.append(new_client)
					else:
					#the message content is the new client's address = ip+port (received as list, not as tuple)
						message_content[0] = unicodedata.normalize('NFKD', message_content[0]).encode('ascii','ignore')
						new_client = ClientModel('', (message_content[0], message_content[1]))
						if new_client not in this_server.list_of_clients:
							this_server.list_of_clients.append(new_client)

			
					sender_id[0] = unicodedata.normalize('NFKD', sender_id[0]).encode('ascii','ignore')
					print ('[Client update] A new client has joined on server: '+ str(sender_id))
					print ('[Client update] The current connected clients in the system are:')
					this_server.showConnectedClients()

				if(message_type == MessageType.LEFTROOM):
				#the message content is the new client's address = ip+port (received as list, not as tuple)
					message_content[0] = unicodedata.normalize('NFKD', message_content[0]).encode('ascii','ignore')
					old_client = ClientModel('', (message_content[0], message_content[1]))
				#Remove this client from the list of clients
					this_server.list_of_clients = this_server.disconnectClient(old_client)
				#show results on server side
					print ('[Client update] Client ' + str(old_client.address) + ' has left. The current logged in clients are:')
					this_server.showConnectedClients()

