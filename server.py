#used for reading process arguments
import sys
##Socket allows for inter-process communication regardless they run on the same machine or on different machines. 
##It uses UNIX file descriptors, as I/O operations are done by opening, reading from/ writing to and close file which has an unique ID (file descriptor).
#import socket package
import socket
#used for selecting sockets in socket list
import select
#used for message serialization
import json
#used to parse unicode received IP addresses
import unicodedata
import datetime
import types
#import classes
from UDPServerModel import UDPServerModel
from DataPacketModel import DataPacketModel
from ClientModel import ClientModel
from MessageUtil import MessageUtil
from Enum import MessageType,SenderType
from MessageHistoryModel import MessageHistoryModel

#store the info about the servers. It includes all servers (also self)
list_of_servers = list()

#get current server datetime
def getCurrentServerDateTime():
	return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#list of servers related operations
#if the server goes down, remove it from the list of servers
def disconnectServer(removed_server):
	if list_of_servers and self != removed_server:
		return [server for server in list_of_servers if server != removed_server]
	else:
		return []
#display the port and ip of the other servers
def showConnectedServers():
	if list_of_servers:
		for server in list_of_servers:
			print ("   ",(server.ip, server.port),"joiningdatetime: ", server.getJoiningDateTime(), " lastsendingmessagedatetime:",server.getLastSendingMessageDateTime())
	else:
		print ('[Server update] No other servers are currently connected to this server:', self.ip)

def getConnectedServersAddresses():
	if list_of_servers:
		return [server.getAddress() for server in list_of_servers if server.default == 0]
	else:
		return []

def multicastMessageToServers(message_type, message_content, message_datetime):
	#for server in list_of_servers:	#getAddress to send msg to
		#if server != this_server:
	this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, message_type, message_content, message_datetime), this_server.getDiscoveryAddress())

#used to send message to one entity server/client
def unicastMessage(message_type, message_content, message_datetime, target_address):
	this_server.socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, message_type, message_content, message_datetime), target_address)


#set message buffer size
message_buffer_size = 2048
localhost = '127.0.0.1'

#set list of message history
lst_messagehistory = []

#create server instance, on localhost, to handle client data exchange (with client, but also with servers)
this_server = UDPServerModel(localhost, int (sys.argv[1]))
#append server joining time and last sending message time
this_server.setJoiningDateTime(MessageUtil.convertStringToDateTime(getCurrentServerDateTime()))
#for this server instance, initialize the discovery socket 
this_server.initializeDiscoverySocket()
#open server general socket
this_server.openSocket()
#append this_server instance to its own list of servers
list_of_servers.append(this_server)


#inform the admin that this server is up
print('[Server update] Server is starting up on %s port %s' % (this_server.ip, this_server.port))	

while True:
	socket_list = [this_server.socket, this_server.discovery_socket]

	read_sockets, write_sockets, error_sockets = select.select([], socket_list, [])
	#firstly, announce the others in the multicast group about this instance's existence sending port (argv[1]) as data
	for socket in write_sockets:
		if socket == this_server.discovery_socket:
			message_datetime = getCurrentServerDateTime()
			this_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(message_datetime))
			#send message with this server's id, specifying that comes from a server entity, that the server is up and giving the port as message
			###the message is sent continuously, by each running server
			this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.SERVERUP, \
				MessageUtil.convertDateTimeToString(this_server.getJoiningDateTime()), message_datetime), this_server.getDiscoveryAddress())

	#read data received on both sockets
	read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])
	for socket in read_sockets:
		if socket == this_server.discovery_socket:
			#store the packet received on the discovery socket, by getting the address and the packet itself returned by 'recvfrom'
			#received_address is the discovery address and is the same for all server instances
			#create a packet object
			temp_packet = DataPacketModel(getCurrentServerDateTime())
			temp_packet.sender_packet, temp_packet.sender_address = this_server.discovery_socket.recvfrom(message_buffer_size)
			
			#extract data from received packet and store it in local object
			temp_packet.extractData()
			
			if isinstance(temp_packet.message_content, list):
				temp_packet.message_content[0] = unicodedata.normalize('NFKD', temp_packet.message_content[0]).encode('ascii','ignore')
				temp_packet.message_content = (temp_packet.message_content[0], temp_packet.message_content[1])

			#discard own message
			if this_server.port != temp_packet.sender_id:
				#add packet in message queue
				if temp_packet not in this_server.received_messages_queue:
					this_server.received_messages_queue.append(temp_packet)
			#if received own message, verify if the other received it, before remove it from the sending queue
			else:
				#check if the other servers sent an ACK
				
				#remove processed packet from the received_messages_queue
				if this_server.sending_messages_queue:
					if temp_packet in this_server.sending_messages_queue:
						this_server.sending_messages_queue.remove(temp_packet)

		if socket == this_server.socket:
		##Recvfrom takes as input message buffer size = the maximum length for the received message
		##it outputs a pair: first is the data = the message; the second is the socket's address
			#create a packet object
			temp_packet = DataPacketModel(getCurrentServerDateTime())
			#read data from socket
			temp_packet.sender_packet, temp_packet.sender_address = this_server.socket.recvfrom(message_buffer_size)
			
			#extract data from received packet and store it in local object
			temp_packet.extractData()

			#discard own message
			if this_server.port != temp_packet.sender_id:
				#add packet in message queue
				if temp_packet not in this_server.received_messages_queue:
					this_server.received_messages_queue.append(temp_packet)

	#once packets were read from sockets and appended to this_server message queue, the message queue is sorted based on sendingDateTime
	this_server.received_messages_queue.sort(key=lambda packet: packet.sendingDateTime)
	
	#process received packets
	for packet in this_server.received_messages_queue:
		#print packet.sendingDateTime
		#if a packet was sent by a server
		if(packet.sender_type == SenderType.SERVER):
			#create a temporary server model with the received attributes
			temp_server = UDPServerModel(localhost, temp_packet.sender_id)
			#this server records the time of the last received packet from any servers connected in the multicast group. Actually, it is the time the packet was sent
			temp_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(str(packet.sendingDateTime)))
			
			#For each received message, that is not acknowledgement, inform the sender server that its message was received \
			#by building a similar packet but with mesage type = RECEIVEDMESAGE. Then, it is unicasted to the sender
			if(packet.message_type != MessageType.RECEIVEDVMESAGE):
				#set time when ack message is issued
				sending_packet = DataPacketModel(getCurrentServerDateTime())
				sending_packet.buildPacket(temp_server.getAddress(), SenderType.SERVER, MessageType.RECEIVEDVMESAGE, packet.message_content, packet.sendingDateTime, this_server.port)
				this_server.sending_messages_queue.append(sending_packet)
			
			#Handle acknowledgements from other servers. This hapeens whena message is issued
			#if(packet.message_type == MessageType.RECEIVEDVMESAGE):
			
			###for the time being, this verification is redundant, since all servers sent SERVERUP continuously but not other message type. 
			if(packet.message_type == MessageType.SERVERUP ):
				#If the server that sent the message is not in this server's group view, add it (remove duplicate message tactic)
				if temp_server not in list_of_servers:
					#Each time a SERVERUP message is sent, it's content has the jointime of the server which sent the packet. 
					#Now, for temp_server, the joiningDateTime  = lastSendingMessageTime
					print "ServerUp", packet.receivedDateTime, packet.message_content 
					temp_server.setJoiningDateTime(MessageUtil.convertStringToDateTime(packet.message_content))
					list_of_servers.append(temp_server)
					print ('[Server update] A server is up. It runs on the address: ' + str(temp_server.getAddress()))

					#send to the newly added server the list of connected clients (if any clients) using the general socket
					if (this_server.list_of_clients):
						#the oldest_server logic to be removed once voting is implemented
						oldest_server = this_server
						for server in list_of_servers:
							if server != this_server:
								if temp_server.joiningdatetime < this_server.joiningdatetime:
									#another server instance is the oldest
									oldest_server = server
						#this server unicasts the message only if it is the oldest
						if oldest_server == this_server:
							#unicastMessage(MessageType.JOINROOM, this_server.getConnectedClientsAddresses(), str(getCurrentServerDateTime()), temp_server.getAddress())
							#create a packet with data to be sent and append it to the list. It is initialized to have the receivingDataTime = sendingDateTime
							sending_packet = DataPacketModel(getCurrentServerDateTime())
							sending_packet.buildPacket(temp_server.getAddress(), SenderType.SERVER, MessageType.JOINROOM, this_server.getConnectedClientsAddresses(), \
							getCurrentServerDateTime(), this_server.port)
							this_server.sending_messages_queue.append(sending_packet)

					#inform the admin about the current connected servers (inform that the list of servers has been updated)
					print ('[Server update] The current running servers are:')
					showConnectedServers()		
			
			#If a new client has connected to another server instance or if this_server joined later, it gets the attributes of the client(s) from the other servers	
			if(packet.message_type == MessageType.JOINROOM):
				#If this_server joined later, it gets a list of more clients as message_content
				if all(isinstance(elem, list) for elem in packet.message_content):
					for client_address in packet.message_content:
					#Get each client's address = ip + port, that is received as list, not as tuple
						client_ip = unicodedata.normalize('NFKD', client_address[0]).encode('ascii','ignore')
						#Create a client object
						new_client = ClientModel('', (client_ip, client_address[1]))
						#If the client is not in this_server's clients group view, add it (remove duplicate message tactic)
						if new_client not in this_server.list_of_clients:
							this_server.list_of_clients.append(new_client)
						
						#inform the admin
						print ('[Client update] There are ' + str(len(packet.message_content)) + ' client(s) connected in the system') 
				else:
				#If this server is running and a new client joined on another running server, the message content is the new client's address = ip+port (received as list, not as tuple)
					if isinstance(packet.message_content, unicode):
						packet.message_content[0] = unicodedata.normalize('NFKD', packet.message_content[0]).encode('ascii','ignore')
					new_client = ClientModel('', (packet.message_content[0], packet.message_content[1]))
					#Add the client in the list, but firstly check if it's there (remove duplicate message tactic)	
					if new_client not in this_server.list_of_clients:
						this_server.list_of_clients.append(new_client)
						
					#inform the admin		
					sender_id = packet.sender_id
					#sender_id[0] = unicodedata.normalize('NFKD', sender_id[0]).encode('ascii','ignore')
					print ('[Client update] A new client has joined on server: '+ str(sender_id))
				
				#show to admin all connected clients	
				print ('[Client update] The currently connected clients in the system are:')
				this_server.showConnectedClients()
			
			if(packet.message_type == MessageType.LEFTROOM):
				#the message content is the new client's address = ip+port (received as list, not as tuple)
				msg_content = packet.message_content
				if isinstance(packet.message_content, unicode):
					msg_content[0] = unicodedata.normalize('NFKD', msg_content[0]).encode('ascii','ignore')
				old_client = ClientModel('', (msg_content[0], msg_content[1]))
				#Remove this client from the list of clients
				this_server.list_of_clients = this_server.disconnectClient(old_client)
				#show results on server side
				print ('[Client update] Client ' + str(old_client.address) + ' has left. The current logged in clients are:')
				this_server.showConnectedClients() 
				
		#handle communication with the clients
		if (packet.sender_type == SenderType.CLIENT):
			#Each time a message is received from a client, create a temporary client object with the received attributes(message + address)
			temp_client = ClientModel(packet.message_content, packet.sender_address)

			#if a new client has joined the conversation
			if (packet.message_type == MessageType.JOINROOM):
				#record joining datetime
				temp_client.setJoiningDateTime(packet.receivedDateTime)
				#append the new client to the list
				this_server.list_of_clients.append(temp_client)

				#show the entire list of available connections
				print ('[Client update] A new client has joined on this server, using the address ' + str(temp_client.address) + '. The current logged in clients are:')
				for client in this_server.list_of_clients:
					print ("   ",(client.address))

				#build a packet
				server_packet = DataPacketModel(getCurrentServerDateTime())
				#send message to the other server instances to inform them that a new client has connected as they need to update their client group view
				#multicastMessageToServers(MessageType.JOINROOM, packet.sender_address, packet.receivedDateTime)
				server_packet.buildPacket("recv from client", SenderType.SERVER, MessageType.JOINROOM, packet.sender_address, packet.receivedDateTime, this_server.port)
				this_server.sending_messages_queue.append(server_packet)
				
				#build a packet
				client_packet = DataPacketModel(getCurrentServerDateTime())
				#send message to the other connected clients
				#this_server.multicastMessagetoClients(temp_client, MessageType.JOINROOM, packet.receivedDateTime)
				client_packet.buildPacket(temp_client, SenderType.CLIENT, MessageType.JOINROOM, packet.sender_address, packet.receivedDateTime, this_server.port)
				this_server.sending_messages_queue.append(client_packet)
				
			#If the client quit the chat, the client application sends a 'quit' message.
			if (packet.message_type == MessageType.LEFTROOM):
				#make sure the client attributes are in this_server's client group view
				if this_server.isClientInList(temp_client):
					#record leving datetime
					temp_client.setLeavingDateTime(temp_packet.receivedDateTime)
					
					#build a packet
					server_packet = DataPacketModel(getCurrentServerDateTime())
					#send message to the other server instances to inform them that a new client has left as they need to update their client group view
					#multicastMessageToServers(MessageType.LEFTROOM, packet.sender_address, packet.receivedDateTime)
					server_packet.buildPacket("recv from client", SenderType.SERVER, MessageType.LEFTROOM, packet.sender_address, packet.receivedDateTime, this_server.port)
					this_server.sending_messages_queue.append(server_packet)
					
					#build a packet
					client_packet = DataPacketModel(getCurrentServerDateTime())
					#notify the other clients
					#this_server.multicastMessagetoClients(temp_client, MessageType.LEFTROOM, packet.receivedDateTime)
					client_packet.buildPacket(temp_client, SenderType.CLIENT, MessageType.LEFTROOM, packet.sender_address, packet.receivedDateTime, this_server.port)
					this_server.sending_messages_queue.append(client_packet)
				
					#Remove this client from the list of clients
					this_server.list_of_clients = this_server.disconnectClient(temp_client)

					#show results on server side
					print ('[Client update] Client ' + str(temp_client.address) + ' has left. The current logged in clients are:')
					this_server.showConnectedClients()
			
			#If the client sent a message to the chat room
			if (packet.message_type == MessageType.NORMALCHAT):
				#make sure the client attributes are in this_server's client group view
				if this_server.isClientInList(temp_client):		
					#append the message to the message history list
					lst_messagehistory.append(MessageHistoryModel(packet.message_content,packet.receivedDateTime,temp_client))
					#record message datetime
					temp_client.setMessageDateTime(packet.receivedDateTime)
					#update his message in list, as only the last message matters. Also, the message was previously updated in the local variable existing_client
					for client in this_server.list_of_clients:
						if client == temp_client:
							client.setMessage(temp_client.message)
					#send message to the other connected clients
					#this_server.multicastMessagetoClients(temp_client, MessageType.NORMALCHAT, packet.receivedDateTime)
					client_packet.buildPacket(temp_client, SenderType.CLIENT, MessageType.NORMALCHAT, packet.sender_address, packet.receivedDateTime, this_server.port)
					this_server.sending_messages_queue.append(client_packet)

		#remove processed packet from the received_messages_queue
		this_server.received_messages_queue.remove(packet)
		
	#this_server.sending_messages_queue.sort(key=lambda packet: packet.sendingDateTime)	
	
	for packet in this_server.sending_messages_queue:
		#print "Sending", packet.sender_id, packet.sender_type, packet.sendingDateTime, packet.receivedDateTime
		if packet.sender_type == SenderType.SERVER:
			if packet.metadata == "recv from client":
				multicastMessageToServers(packet.message_type, packet.message_content, packet.sendingDateTime)
				
			else:
				unicastMessage(packet.message_type, packet.message_content, packet.sendingDateTime, packet.metadata)
				this_server.sending_messages_queue.remove(packet)
		
		if packet.sender_type == SenderType.CLIENT:
			this_server.multicastMessagetoClients(packet.metadata, packet.message_type, packet.sendingDateTime)
			this_server.sending_messages_queue.remove(packet)
