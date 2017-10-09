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
from threading import Thread
from time import sleep
#import classes
from UDPServerModel import UDPServerModel
from ClientModel import ClientModel
from MessageUtil import MessageUtil
from Enum import MessageType,SenderType,ConstantValues
from MessageHistoryModel import MessageHistoryModel
from GlobalInfo import GlobalInfo

isabletopingtheleader = True
checktheleader = True

#store the info about the other servers. It includes all servers.
list_of_servers = list()

#create global info
global_info = GlobalInfo()

#get current server datetime
def getCurrentServerDateTime():
	return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#list of servers related operations

#if the server goes down, remove it from the list of servers
def disconnectServer(self, removed_server):
	if list_of_servers and self != removed_server:
		return [server for server in list_of_servers if server != removed_server]
	else:
		return []
#display the port and ip of the other servers
def showConnectedServers(self):
	if list_of_servers:
		for server in list_of_servers:
			print ("   ",(server.ip, server.port),"joiningdatetime: ", server.getJoiningDateTime(), " lastsendingmessagedatetime:",server.getLastSendingMessageDateTime(), "is active:", server.isActive())
	else:
		print ('[Server update] No other servers are currently connected to this server:', self.ip)

def getConnectedServersAddresses(self):
	if list_of_servers:
		return [server.getAddress() for server in list_of_servers if server.default == 0]
	else:
		return []

def getStrListOfConnectedServers():
	strserver = ""
	if list_of_servers:
		lst_size = len(list_of_servers)
		idx = 0
		for sv in list_of_servers:
			is_server_leader = 0
			is_server_active = 0
			if (sv.isTheLeader()):
				is_server_leader = 1
			if (sv.isActive()):
				is_server_active = 1

			if(idx == lst_size-1):
				strserver = strserver + str(sv.port)+"#"+MessageUtil.convertDateTimeToString(sv.getJoiningDateTime())+"#"+MessageUtil.convertDateTimeToString(sv.getLastSendingMessageDateTime())+"#"+str(is_server_leader)+"#"+str(is_server_active)
			else:
				strserver = strserver + str(sv.port)+"#"+MessageUtil.convertDateTimeToString(sv.getJoiningDateTime())+"#"+MessageUtil.convertDateTimeToString(sv.getLastSendingMessageDateTime())+"#"+str(is_server_leader)+"#"+str(is_server_active)+";"
			idx = idx+1
	return strserver

def getLitsOfServerPorts():
	lst_server_ports = []
	for server_item in list_of_servers:
		lst_server_ports.append(server_item.port)

	return lst_server_ports

def getTheLeader():
	theleader = None
	if (global_info.getCurrentLeader() is not None):
		for server_item in list_of_servers:
			if (server_item.port == global_info.getCurrentLeader()):
				theleader = server_item
				break
	return theleader

def getActiveServers():
	lst_available_servers = []
	for server_item in list_of_servers:
		if (server_item.isActive()):
			lst_available_servers.append(server_item)
	return lst_available_servers

def getServerByPort(_port):
	single_server = None
	for server_item in getActiveServers():
		if (server_item.port == _port):
			single_server = server_item
			break
	return single_server


def getExisitngServerByPort(_port):
	single_server = None
	for server_item in list_of_servers:
		if (server_item.port == _port):
			single_server = server_item
			break
	return single_server


def removeTheLeader():
	print ("------------ removing the old leader------------------------")
	for i, server in enumerate(list_of_servers):
		# print(server.port, global_info.getCurrentLeader())
		if server.port == global_info.getCurrentLeader():
			list_of_servers[i].deactivateTheRoleAsTheLeader()
			list_of_servers[i].deactivateServer()
			# del list_of_servers[i]
			break

def resetLastSendingMessageDateTimeAllServers():
	for server_item in getActiveServers():
		server_item.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(getCurrentServerDateTime()))

def updateSenderLastSendingMessageDateTime(_port, _lastsendingmessagedatetime):
	active_servers = getActiveServers()
	if (len(active_servers) > 1):
		sender_server = getServerByPort(_port)
		if (sender_server is not None):
			sender_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(_lastsendingmessagedatetime))

def multicastMessageToServers(self, message_type, message_content, message_datetime):
	for server in list_of_servers:	#getAddress to send msg to
		if server != self:
			self.socket.sendto(MessageUtil.constructMessage(self.getAddress(), SenderType.SERVER, message_type, message_content, message_datetime), server.getAddress())

#used to send message to one entity server/client
def unicastMessage(self, message_type, message_content, message_datetime, target_address):
	self.socket.sendto(MessageUtil.constructMessage(self.getAddress(), SenderType.SERVER, message_type, message_content, message_datetime), target_address)


#set message buffer size
message_buffer_size = 2048
localhost = '127.0.0.1'

#set list of message history
lst_messagehistory = []
#create server instance, on localhost, to handle client data exchange (with client, but also with servers)
this_server = UDPServerModel(localhost, int (sys.argv[1]))
#append server joining time and last sending message time
this_server.setJoiningDateTime(MessageUtil.convertStringToDateTime(getCurrentServerDateTime()))
#set global info status
global_info.setServerStatus(MessageType.SERVERUP)
#set server is active
this_server.activateServer()
#open server general socket
this_server.openSocket()
#for this server instance, initialize the discovery socket 
this_server.initializeDiscoverySocket()
#append this_server instance to its own list of servers
list_of_servers.append(this_server)

#inform the admin that this server is up
print('[Server update] Server is starting up on %s port %s' % (this_server.ip, this_server.port))

#define the socket list
socket_list = [this_server.socket, this_server.discovery_socket]

#set thread and timer
def thread_decideLeader():
	#starting thread
	sleep(10)
	#Decide the leader or the voting after 20 seconds
	if(global_info.getServerStatus() == MessageType.SERVERUP):
		#reset lastsendingmessagedatetime for all servers
		resetLastSendingMessageDateTimeAllServers()
		#get active servers
		lst_active_servers = getActiveServers()
		#sort servers by joining time and port
		sorted_list_of_server_by_joining_time = sorted(lst_active_servers, key=lambda x: x.joiningdatetime, reverse=True)
		sorted_list_of_server_by_port = sorted(lst_active_servers, key=lambda x: x.port, reverse=True)

		#if my joined times is greater than the others, then tell everyone that the leader is the one who has highest port
		if(sorted_list_of_server_by_joining_time[len(sorted_list_of_server_by_joining_time)-1] == this_server):
			#launch the leader
			print("============================ I will launch the leader ================================")
			#update the global info and deactivate my role as leader
			global_info.setServerStatus(MessageType.RUNNING)
			global_info.setCurrentLeader(sorted_list_of_server_by_port[0].port)

			#if it's my ip address and my port, then set I am the leader
			if (sorted_list_of_server_by_port[0].port == this_server.port):
				this_server.activateTheRoleAsTheLeader()
			else:
			#otherwise deactivate my role as the leader
				this_server.deactivateTheRoleAsTheLeader()

			#tell everyone that the leader is the one who has highest port
			this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.DECLARETHELEADER, str(sorted_list_of_server_by_port[0].port), getCurrentServerDateTime()), this_server.getDiscoveryAddress())
			print("the leader is", global_info.getServerStatus(), global_info.getCurrentLeader(), this_server.isTheLeader())
			print("========================== Thread decide leader ended ====================================")


def thread_mainprocess():
	while True:
		read_sockets, write_sockets, error_sockets = select.select([], socket_list, [])

		#firstly, announce the others in the multicast group about this instance's existence sending port (argv[1]) as data
		for socket in write_sockets:
			#multicast to group if server status is SERVERUP or my role is the leader
			if (socket == this_server.discovery_socket and (global_info.getServerStatus() == MessageType.SERVERUP or this_server.isTheLeader())): #and (global_info.getServerStatus() != MessageType.VOTING or global_info.getServerStatus() != MessageType.VOTING):
				message_datetime = getCurrentServerDateTime()
				this_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(message_datetime))
				#if I'm the leader, tell the potential server that I'm the leader so they can update their status
				if (global_info.getServerStatus() == MessageType.RUNNING and this_server.isTheLeader()):
					this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.ANNOUNCELEADERAFTERJOIN, str(this_server.port), getCurrentServerDateTime()), this_server.getDiscoveryAddress())
				else:
					#send message with this server's id, specifying that comes from a server entity, that the server is up and giving the port as message
					this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.SERVERUP, MessageUtil.convertDateTimeToString(this_server.getJoiningDateTime()), message_datetime), this_server.getDiscoveryAddress())


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

				if (sender_type == SenderType.SERVER):
					if sender_port != this_server.port:
						if (global_info.getServerStatus() == MessageType.SERVERUP or this_server.isTheLeader()):
							if (message_type == MessageType.DECLARETHELEADER or message_type == MessageType.ANNOUNCELEADERAFTERJOIN):
								if (global_info.getServerStatus() == MessageType.SERVERUP):
									#if it's my ip address and my port, then set I am the leader
									if (int(message_content) == this_server.port):
										this_server.activateTheRoleAsTheLeader()
									else:
										updateSenderLastSendingMessageDateTime(sender_port, message_datetime)
									#set the params of global info
									global_info.setServerStatus(MessageType.RUNNING)
									global_info.setCurrentLeader(int(message_content))
									print("Voting done. My current global info is: server status:%s and the leader is %s"%(global_info.serverstatus,str(global_info.getCurrentLeader())))

							else:
								#create a temporary server model with the received attributes
								temp_server = UDPServerModel(localhost, sender_port)
								serverdatetime_received_acknowledgement = getCurrentServerDateTime()
								temp_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(message_datetime))
								allowtoaddnewsever = False

								if temp_server.port not in getLitsOfServerPorts():
									temp_server.setJoiningDateTime(MessageUtil.convertStringToDateTime(message_content))
									temp_server.activateServer()
									list_of_servers.append(temp_server)
									allowtoaddnewsever = True
								else:
									#get existing server
									existing_server = getExisitngServerByPort(sender_port)
									if (existing_server.isActive() == False):
										#print("existing server", existing_server.port, existing_server.getJoiningDateTime())
										#check if the previous joiningdatetime is greater than the current joining datetime
										if (MessageUtil.convertStringToDateTime(message_content) > existing_server.getJoiningDateTime()):
											#reactivate the server
											existing_server.setJoiningDateTime(MessageUtil.convertStringToDateTime(message_content))
											existing_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(message_datetime))
											existing_server.activateServer()
											allowtoaddnewsever = True

								#if it is allowed to add new server, then broadcast the message
								if (allowtoaddnewsever):
									print ('[Server update] A new server is up. It runs on the address:%s. My global status is %s'%(str(temp_server.getAddress()), global_info.getServerStatus()))
									#if server is running normally and new server joins the network, then master will exchange the global information
									# print("global_info.getServerStatus()",global_info.getServerStatus(),"this_server.isTheLeader()",this_server.isTheLeader())
									if (global_info.getServerStatus() == MessageType.RUNNING and this_server.isTheLeader()):
										print("==========================I am the leader, I will inform the new connected server=================================")
										#announce that I'm the leader
										print("Sending client %s the announcement that I'm the leader"%(str(temp_server.port)))
										unicastMessage(this_server, MessageType.ANNOUNCELEADERAFTERJOIN, str(this_server.port), serverdatetime_received_acknowledgement, temp_server.getAddress())

										#send the list of existing server to the newly added server
										print("Sending client %s the list of existing servers"%(str(temp_server.port)))
										unicastMessage(this_server, MessageType.LISTOFEXISTINGSERVERS, getStrListOfConnectedServers(), serverdatetime_received_acknowledgement, temp_server.getAddress())

										#send the newly added server to the multicast groups
										print("Sending the multicast message to all connected clients telling that the server %s is up and running"%(str(temp_server.port)))
										this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.NEWSERVER, str(temp_server.port)+"#"+serverdatetime_received_packet, getCurrentServerDateTime()), this_server.getDiscoveryAddress())

										# for ex_server in getActiveServers():
										# 	if (ex_server.port not in (this_server.port,temp_server.port)):
										# 		unicastMessage(this_server, MessageType.NEWSERVER, str(temp_server.port)+"#"+serverdatetime_received_packet, serverdatetime_received_acknowledgement, ex_server.getAddress())


										#send to the newly added server and  the list of connected clients (if any clients) using the general socket
										# if (this_server.list_of_clients):
										# 	unicastMessage(this_server, MessageType.JOINROOM, this_server.getConnectedClientsAddresses(), serverdatetime_received_acknowledgement, temp_server.getAddress())

									#inform the admin about the current connected servers (inform that the list of servers has been updated)
									print ('[Server update] The current running servers are:')
									showConnectedServers(this_server)
						else:
							#if a new server is up
							if(message_type == MessageType.NEWSERVER):
								print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
								arr_messagecontent= message_content.split("#")
								arr_messagecontent_port = int(arr_messagecontent[0])
								arr_messagecontent_joiningdate = MessageUtil.convertStringToDateTime(arr_messagecontent[1])

								#if it's not my port, then add to the server list
								if (arr_messagecontent_port not in [this_server.port]):
									newly_added_server = UDPServerModel(localhost,arr_messagecontent_port)
									newly_added_server.setJoiningDateTime(arr_messagecontent_joiningdate)
									newly_added_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(serverdatetime_received_acknowledgement))
									newly_added_server.activateServer()

									if newly_added_server.port not in getLitsOfServerPorts():
										list_of_servers.append(newly_added_server)
									else:
										#get existing server and activate its current status to true and update the joiningdatetime and lastsendingmessagedatetime
										existing_server = getExisitngServerByPort(arr_messagecontent_port)
										existing_server.activateServer()
										existing_server.setJoiningDateTime(arr_messagecontent_joiningdate)
										existing_server.setLastSendingMessageDateTime(arr_messagecontent_joiningdate)

									#update the sending messagedatetime of the sender
									updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)
									print("New server with port %s joined the system"%(str(newly_added_server.port)))
									showConnectedServers(this_server)
								else:
									print("I ignore the message since It's me that up")

							#if slave goes down
							if (message_type == MessageType.SLAVEDOWN):
								print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
								#update my server list
								unavailable_server = getExisitngServerByPort(int(message_content))
								if (unavailable_server is not None):
									#update the unvaialable server status to inactive
									unavailable_server.deactivateServer()
								print("I have updated my server list.")
								showConnectedServers(this_server)

							#if there is an announcement of the new leader
							if (message_type == MessageType.ANNOUNCELEADER):
								print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
								#remove the previous leader
								removeTheLeader()

								#set the params of global info
								global_info.setServerStatus(MessageType.RUNNING)
								global_info.setCurrentLeader(int(message_content))

								#update the last sending message datetime of the sender
								updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)
								print("This is my current global info:%s, current leader:%s"%(global_info.getServerStatus(), str(global_info.getCurrentLeader())))


			if socket == this_server.socket:
				#Recvfrom takes as input message buffer size = the maximum length for the received message
				#it outputs a pair: first is the data = the message; the second is the socket's address
				#read data from socket. At this moment is not known whether data belongs to a client or to a server
				received_packet, received_address = this_server.socket.recvfrom(message_buffer_size)
				serverdatetime_received_packet = getCurrentServerDateTime()
				#extract data from packet
				sender_id, sender_type, message_type, message_content, message_datetime = MessageUtil.extractMessage(received_packet)

			# 	#handle communication with the clients
			# 	if (sender_type == SenderType.CLIENT):
			# 	#Each time a message is received from a client, create a temporary client with the received attributes(message + address)
			# 		temp_client = ClientModel(message_content, received_address)
            #
			# 		#if a new client has joined the conversation
			# 		if (message_type == MessageType.JOINROOM):
			# 		#record joining datetime
			# 			temp_client.setJoiningDateTime(serverdatetime_received_packet)
			# 		#append the new client to the list
			# 			this_server.list_of_clients.append(temp_client)
            #
			# 		#show the entire list of available connections
			# 			print ('[Client update] A new client has joined on this server, using the address ' + str(temp_client.address) + '. The current logged in clients are:')
			# 			for client in this_server.list_of_clients:
			# 				print ("   ",(client.address))
            #
			# 		#send message to the other server instances to inform them that a new client has connected as they need to update their client group view
			# 			multicastMessageToServers(this_server, MessageType.JOINROOM, received_address, serverdatetime_received_packet)
			# 		#send message to the other connected clients
			# 			this_server.multicastMessagetoClients(temp_client, MessageType.JOINROOM, serverdatetime_received_packet)
			# 		else:
			# 			if this_server.isClientInList(temp_client):
			# 				# if he exited, the client application sends a 'quit' message.
			# 				if (message_type == MessageType.LEFTROOM):
			# 				#record leving datetime
			# 					temp_client.setLeavingDateTime(serverdatetime_received_packet)
			# 				#send message to the other server instances to inform them that a new client has left as they need to update their client group view
			# 					multicastMessageToServers(this_server, MessageType.LEFTROOM, received_address, serverdatetime_received_packet)
			# 				#notify the other clients
			# 					this_server.multicastMessagetoClients(temp_client, MessageType.LEFTROOM, serverdatetime_received_packet)
			# 				#Remove this client from the list of clients
			# 					this_server.list_of_clients = this_server.disconnectClient(temp_client)
            #
			# 				#show results on server side
			# 					print ('[Client update] Client ' + str(temp_client.address) + ' has left. The current logged in clients are:')
			# 					this_server.showConnectedClients()
			# 				#if it is an existing client and if it didn't quit
			# 				else:
			# 				#append to message to the message history list
			# 					lst_messagehistory.append(MessageHistoryModel(message_content,serverdatetime_received_packet,temp_client))
			# 				#record message datetime
			# 					temp_client.setMessageDateTime(serverdatetime_received_packet)
			# 				#update his message in list, as only the last message matters. Also, the message was previously updated in the local variable existing_client
			# 					for client in this_server.list_of_clients:
			# 						if client == temp_client:
			# 							client.setMessage(temp_client.message)
			# 				#send message to the other connected clients
			# 					this_server.multicastMessagetoClients(temp_client, MessageType.NORMALCHAT, serverdatetime_received_packet)
            #
			# 				#print message history
			# 					print("------------------- History of the message---------------------------")
			# 					for msg in lst_messagehistory:
			# 						print(msg.message, msg.messagedatetime, msg.ClientModel.address)
            #
				# #handle communication with other servers
				if (sender_type == SenderType.SERVER):
					#if not the same port
					if (int(sender_id[1]) != this_server.port):
						#if a server sent a message, create a server instance considering the receieved address (ip + port)
						temp_server = UDPServerModel(received_address[0], received_address[1])
						serverdatetime_received_acknowledgement = getCurrentServerDateTime()

						if (message_type == MessageType.LISTOFEXISTINGSERVERS):
							print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
							arr_existing_servers = message_content.split(";")

							for item_arr in arr_existing_servers:
								item_server_arr = item_arr.split("#")
								item_server_port = int(item_server_arr[0])
								item_server_joiningtime = MessageUtil.convertStringToDateTime(item_server_arr[1])
								item_server_lastsendingmessage = MessageUtil.convertStringToDateTime(item_server_arr[2])

								item_arr_server_obj = UDPServerModel(localhost,item_server_port)
								item_arr_server_obj.setJoiningDateTime(item_server_joiningtime)
								item_arr_server_obj.setLastSendingMessageDateTime(item_server_lastsendingmessage)
								if int(item_server_arr[3]) == 1:
									item_arr_server_obj.activateTheRoleAsTheLeader()
								if int(item_server_arr[4]) == 1:
									item_arr_server_obj.activateServer()

								#if server not in the list, then add
								if (item_server_port not in getLitsOfServerPorts()):
									list_of_servers.append(item_arr_server_obj)
								else:
									#get existing server and activate its current status to true and update the joiningdatetime and lastsendingmessagedatetime
									existing_server = getExisitngServerByPort(item_server_port)
									existing_server.activateServer()
									existing_server.setJoiningDateTime(item_server_joiningtime)
									existing_server.setLastSendingMessageDateTime(item_server_lastsendingmessage)

							#update the last sending message datetime of the sender
							updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)
							#show current list of servers
							showConnectedServers(this_server)
							print("List of servers has been updated")

						#if a new client has connected to another server instance, update local list_of_clients
						if(message_type == MessageType.JOINROOM):
							print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
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

							#update the last sending message datetime of the sender
							updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)
							this_server.showConnectedClients()

						if(message_type == MessageType.LEFTROOM):
							print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
							#the message content is the new client's address = ip+port (received as list, not as tuple)
							message_content[0] = unicodedata.normalize('NFKD', message_content[0]).encode('ascii','ignore')
							old_client = ClientModel('', (message_content[0], message_content[1]))
							#Remove this client from the list of clients
							this_server.list_of_clients = this_server.disconnectClient(old_client)
							#show results on server side
							print ('[Client update] Client ' + str(old_client.address) + ' has left. The current logged in clients are:')
							#update the last sending message datetime of the sender
							updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)
							this_server.showConnectedClients()

						if (message_type == MessageType.ANNOUNCELEADERAFTERJOIN):
							print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
							#set the params of global info
							global_info.setServerStatus(MessageType.RUNNING)
							global_info.setCurrentLeader(int(message_content))

							#update the last sending message datetime of the sender
							updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)
							print("This is my current global info:%s, current leader:%s"%(global_info.getServerStatus(), str(global_info.getCurrentLeader())))


						if (this_server.isTheLeader() and message_type == MessageType.PINGTHELEADER):
							#Since I'm the leader who got this message, therefore I should reply it to indicate that I'm alive
							unicastMessage(this_server, MessageType.ACKNOWLEDGEMENTPINGTHELEADER, '', getCurrentServerDateTime(), received_address)
							#update the last sending message datetime of the sender
							updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)

						if (this_server.isTheLeader() == False and message_type == MessageType.ACKNOWLEDGEMENTPINGTHELEADER):
							#update the the property LastSendingMessageDateTime of the leader
							getTheLeader().setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(message_datetime))
							#update the last sending message datetime of the sender
							updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)

						if (message_type == MessageType.VOTING):
							print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))

							#if the leader has been changed
							if (int(message_content) == global_info.getCurrentLeader()):
								global_info.setServerStatus(MessageType.VOTING)
								unicastMessage(this_server, MessageType.ACKNOWLEDGEMENTVOTING, '', getCurrentServerDateTime(), received_address)
								#remove the previous leader
								removeTheLeader()

								#sort the members by port
								sorted_list_of_server_by_port = sorted(getActiveServers(), key=lambda x: x.port, reverse=True)

								#if the members only one or my port is the highest among others then I'm the leader
								if (sorted_list_of_server_by_port[0].port == this_server.port):
									this_server.activateTheRoleAsTheLeader()
									global_info.setCurrentLeader(this_server.port)
									global_info.setServerStatus(MessageType.RUNNING)

									#announce that I'm the leader by sending message to multicast group
									this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.ANNOUNCELEADER, str(this_server.port), getCurrentServerDateTime()), this_server.getDiscoveryAddress())

									# for server_item in getActiveServers():
									# 	unicastMessage(this_server, MessageType.ANNOUNCELEADER, str(this_server.port), getCurrentServerDateTime(), server_item.getAddress())
							else:
								#send the current leader to the sender
								unicastMessage(this_server, MessageType.ANNOUNCELEADER, str(global_info.getCurrentLeader()), getCurrentServerDateTime(), received_address)

							#update the last sending message datetime of the sender
							updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)

						if (message_type == MessageType.ACKNOWLEDGEMENTVOTING):
							print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
							global_info.setServerStatus(MessageType.ACKNOWLEDGEMENTVOTING)
							#update the last sending message datetime of the sender
							updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)


						if (message_type == MessageType.PAUSERUNNING):
							print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
							global_info.setServerStatus(MessageType.PAUSERUNNING)
							#update the last sending message datetime of the sender
							updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)

						if (message_type == MessageType.PINGTHESLAVE):
							print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
							#I will reply it
							unicastMessage(this_server, MessageType.ACKNOWLEDGEMENTPINGTHESLAVE, "", getCurrentServerDateTime(), received_address)
							#update the last sending message datetime of the sender
							updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)

						if (message_type == MessageType.ACKNOWLEDGEMENTPINGTHESLAVE):
							print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
							#update the last sending message datetime of the sender
							updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)


def thread_ping_leader():
	global isabletopingtheleader
	while True:
		#if I am not the leader and the servers are running normally
		if (this_server.isTheLeader() == False and getTheLeader() is not None  and global_info.getServerStatus() == MessageType.RUNNING and len(list_of_servers) > 1):
			#if I'm not the leader, so I will ping the leader
			if (isabletopingtheleader):
				print("**************** ping the leader *******************")
				unicastMessage(this_server, MessageType.PINGTHELEADER, '', getCurrentServerDateTime(), getTheLeader().getAddress())
				#deactivate isabletopingleader
				isabletopingtheleader = False
				#set sleeping time to 10
				sleep(5)
				#activate again isabletopingleader
				isabletopingtheleader = True

def thread_launch_election():
	global checktheleader
	while True:
		try:
			#if I am not the leader and the servers are running normally
			if (this_server.isTheLeader() == False and getTheLeader() is not None  and global_info.getServerStatus() == MessageType.RUNNING and len(list_of_servers) > 1 and checktheleader):
				checktheleader = False
				first_theleaderlastdatetimesendingmessage = getTheLeader().getLastSendingMessageDateTime()
				first_delta = (MessageUtil.convertStringToDateTime(getCurrentServerDateTime()) - first_theleaderlastdatetimesendingmessage).total_seconds()
				print("**************** check weather the leader is alive *******************")
				print("First delta:", first_delta)

				#compare delta value with its maximum
				if (first_delta > ConstantValues.DELTAMAX):
					#ping the leader again to make sure he is alive
					unicastMessage(this_server, MessageType.PINGTHELEADER, '', getCurrentServerDateTime(), getTheLeader().getAddress())
					#wait for 15 seconds
					sleep(15)
					#double check again
					second_theleaderlastdatetimesendingmessage = getTheLeader().getLastSendingMessageDateTime()
					second_delta = (MessageUtil.convertStringToDateTime(getCurrentServerDateTime()) - second_theleaderlastdatetimesendingmessage).total_seconds()
					print("second delta %s"%str(second_delta))

					#again, compare delta value with its maximum
					if (second_delta > ConstantValues.DELTAMAX):
						isAbleToPingTheLeader = False
						#set current status to voting
						global_info.setServerStatus(MessageType.PAUSERUNNING)
						#remove the previous leader
						removeTheLeader()

						#sort the members by port
						sorted_list_of_server_by_port = sorted(getActiveServers(), key=lambda x: x.port, reverse=True)

						#if the members only one or my port is the highest among others then I'm the leader
						if (sorted_list_of_server_by_port[0].port == this_server.port):
							this_server.activateTheRoleAsTheLeader()
							global_info.setCurrentLeader(this_server.port)
							global_info.setServerStatus(MessageType.RUNNING)

							#announce that I'm the leader by sending message to multicast group
							this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.ANNOUNCELEADER, str(this_server.port), getCurrentServerDateTime()), this_server.getDiscoveryAddress())
							print("I am the leader now and this is my global info:%s , %s"%(global_info.getServerStatus(), str(global_info.getCurrentLeader())))
						#launch election to the servers who have the higher port than me
						else:
							#if my status still pause running and other servers don't send anything yet, then I'll launch the election

							if (global_info.getServerStatus() == MessageType.PAUSERUNNING):
								#set server status and global status
								global_info.setServerStatus(MessageType.WAITINGFORACKNOWLEDGMENT)

								print("Launching election")
								for server_item in sorted_list_of_server_by_port:
									#send unicast message to the highest ports
									if (server_item.port > this_server.port):
										print("sending unicast message to %s (first attempt)"%(str(server_item.port)))
										unicastMessage(this_server, MessageType.VOTING, str(global_info.getCurrentLeader()), getCurrentServerDateTime(), server_item.getAddress())
									#send the other server to stop working
									else:
										if (server_item.port < this_server.port):
											print("sending unicast message to %s tell them to stop working for a moment"%(str(server_item.port)))
											unicastMessage(this_server, MessageType.PAUSERUNNING, str(global_info.getCurrentLeader()), getCurrentServerDateTime(), server_item.getAddress())
								#wait for 20 seconds
								sleep(20)

								#if for more than 20 seconds, there is no any acknowledgement from the other servers then resend the voting again
								if (global_info.getServerStatus() == MessageType.WAITINGFORACKNOWLEDGMENT):
									for server_item in sorted_list_of_server_by_port:
										#re-send unicast message to the highest ports
										if (server_item.port > this_server.port):
											print("resending unicast message to %s since the server(s) who has the higher port than me dont reply (second attempt)"%(server_item.port))
											unicastMessage(this_server, MessageType.VOTING, str(global_info.getCurrentLeader()), getCurrentServerDateTime(), server_item.getAddress())

								sleep(20)
								#if for more than 20 seconds after retry, there is no any acknowledgement from the other servers then resend the voting again
								if (global_info.getServerStatus() == MessageType.WAITINGFORACKNOWLEDGMENT):
									print("I will declare myself as the leader since nobody cares")
									this_server.activateTheRoleAsTheLeader()
									global_info.setCurrentLeader(this_server.port)

									#announce that I'm the leader by sending message to multicast group
									this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.ANNOUNCELEADER, str(this_server.port), getCurrentServerDateTime()), this_server.getDiscoveryAddress())

									# for server_item in sorted_list_of_server_by_port:
									# 	if (server_item.port is not this_server.port):
									# 		#send announcement to other servers that I'm the leader now
									# 		unicastMessage(this_server, MessageType.ANNOUNCELEADER, str(this_server.port), getCurrentServerDateTime(), server_item.getAddress())

									#set server status and global status
									global_info.setServerStatus(MessageType.RUNNING)
									print("This is my current global info:%s, current leader:%s"%(global_info.getServerStatus(), str(global_info.getCurrentLeader())))
						showConnectedServers(this_server)
		except:
			print("Do not worry, it is going to be fine")
		finally:
			sleep(15)
			checktheleader = True


#ping the slave
def thread_ping_slave(port):
	#get exisiting slave
	existing_slave = getExisitngServerByPort(port)
	#get the first delta of existing server
	first_theslavelastdatetimesendingmessage = existing_slave.getLastSendingMessageDateTime()
	first_delta = (MessageUtil.convertStringToDateTime(getCurrentServerDateTime()) - first_theslavelastdatetimesendingmessage).total_seconds()
	print("checking the slave status %s, first delta:%s"%(str(port),str(first_delta)))

	#compare delta value with its maximum
	if (first_delta > ConstantValues.DELTAMAX):
		unicastMessage(this_server, MessageType.PINGTHESLAVE, '', getCurrentServerDateTime(), existing_slave.getAddress())
		#wait for 15 seconds
		sleep(15)
		#get the second delta of existing server
		second_theslavelastdatetimesendingmessage = getExisitngServerByPort(port).getLastSendingMessageDateTime()
		second_delta = (MessageUtil.convertStringToDateTime(getCurrentServerDateTime()) - second_theslavelastdatetimesendingmessage).total_seconds()
		print("checking the slave status %s, second delta:%s"%(str(port),str(second_delta)))

		#again, compare delta value with its maximum
		if (second_delta > ConstantValues.DELTAMAX):
			#deactivate the slave
			getExisitngServerByPort(port).deactivateServer()

			#send unicast message to all other slaves
			this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.SLAVEDOWN, str(port), getCurrentServerDateTime()), this_server.getDiscoveryAddress())
			print("server %s is going down. The multicast message has been sent to the other servers"%(str(port)))


#check wether the slave is alive
def thread_checking_slaves():
	while True:
		if (this_server.isTheLeader() and global_info.getServerStatus() == MessageType.RUNNING):

			for slave in getActiveServers():
				if slave.port is not global_info.getCurrentLeader():
					#create new thread to chek other slave
					th_slave = Thread(target=thread_ping_slave, args=(slave.port,))
					th_slave.start()

		#sleep or another 20 seconds
		sleep(15)

t1 = Thread(target=thread_mainprocess, args=())
t1.start()

t2 = Thread(target = thread_decideLeader, args = ())
t2.start()

t3 = Thread(target=thread_ping_leader, args=())
t3.start()

t4 = Thread(target=thread_launch_election, args=())
t4.start()

t5 = Thread(target=thread_checking_slaves, args=())
t5.start()
