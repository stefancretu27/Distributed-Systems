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
from Enum import MessageType,SenderType,ConstantValues,MessageContent
from MessageHistoryModel import MessageHistoryModel
from GlobalInfo import GlobalInfo

isabletopingtheleader = True
checktheleader = True
alreadysentmessage = False

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

def deactivateTheLeader():
	print ("------------ deactivate the old leader------------------------")
	for i, server in enumerate(list_of_servers):
		if server.port == global_info.getCurrentLeader():
			list_of_servers[i].deactivateTheRoleAsTheLeader()
			break

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
	global alreadysentmessage
	#starting thread
	sleep(15)
	#set alreadysentmessage to false in to indicate that we're about to launch election. And we don't allow other servers to join
	alreadysentmessage = True
	servercrash = 0

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
			this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.DECLARETHELEADER, str(sorted_list_of_server_by_port[0].port)+"#"+str(servercrash), getCurrentServerDateTime()), this_server.getDiscoveryAddress())
			print("the leader is", global_info.getServerStatus(), global_info.getCurrentLeader(), this_server.isTheLeader())
			print("========================== Thread decide leader ended ====================================")

	if (global_info.getServerStatus() == MessageType.LISTOFSERVERUPDATED):
		#then I'm the leader now since my port is higher than the others
		lst_active_servers = getActiveServers()
		#sort servers by joining time and port
		sorted_list_of_server_by_port = sorted(lst_active_servers, key=lambda x: x.port, reverse=True)
		theleader = sorted_list_of_server_by_port[0]
		if (theleader is not None):
			if (this_server.port == theleader.port):
				theleader = this_server
				print("I am the leader now, and I will announce the message to everyone")
				#tell everyone that I am the leader
				this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.DECLARETHELEADER, str(this_server.port)+"#"+str(servercrash), getCurrentServerDateTime()), this_server.getDiscoveryAddress())
			else:
				print("I don't have the chance to be the leader. So, I will update the leader to %s"%(str(theleader.port)))
			#update my status to running and set I'm the leader
			theleader.activateTheRoleAsTheLeader()
			global_info.setServerStatus(MessageType.RUNNING)
			global_info.setCurrentLeader(theleader.port)


def thread_mainprocess():
	global alreadysentmessage
	while True:
		#read data received on sockets
		read_sockets, write_sockets, error_sockets = select.select([], socket_list, [])
		#firstly, announce the others in the multicast group about this instance's existence sending port (argv[1]) as data
		for socket in write_sockets:
			#multicast to group if server status is SERVERUP or my role is the leader
			if (socket == this_server.discovery_socket and global_info.getServerStatus() == MessageType.SERVERUP and alreadysentmessage == False):#or this_server.isTheLeader())): #and (global_info.getServerStatus() != MessageType.VOTING or global_info.getServerStatus() != MessageType.VOTING):
				message_datetime = getCurrentServerDateTime()
				this_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(message_datetime))
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
						if ((global_info.getServerStatus() == MessageType.SERVERUP or global_info.getServerStatus() == MessageType.RUNNING)):#this_server.isTheLeader() ):
							#if the server is up or running and new server is joining
							if ((global_info.getServerStatus() == MessageType.SERVERUP or global_info.getServerStatus() == MessageType.RUNNING) and message_type == MessageType.SERVERUP):
								print("global_info.getServerStatus()", global_info.getServerStatus(), "message type", message_type)
								#create a temporary server model with the received attributes
								temp_server = UDPServerModel(localhost, sender_port)
								serverdatetime_received_acknowledgement = getCurrentServerDateTime()
								temp_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(message_datetime))
								allowtoaddnewsever = False


								print("list of server", len(getLitsOfServerPorts()), "port baru", temp_server.port)
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

								print("====================", allowtoaddnewsever, "===================", global_info.getServerStatus())
								#if it is allowed to add new server, then broadcast the message
								if (allowtoaddnewsever == True and global_info.getServerStatus() == MessageType.RUNNING):
									#send acknowledgement to the newly added server
									print("I send acknowledgement message to the newly added server")
									unicastMessage(this_server, MessageType.ACKNOWLEDGEMENTFROMALIVESERVER, '', serverdatetime_received_acknowledgement, temp_server.getAddress())

								print ('[Server update] A new server is up. It runs on the address:%s. My global status is %s'%(str(temp_server.getAddress()), global_info.getServerStatus()))
								print ('[Server update] The current running servers are:')
								showConnectedServers(this_server)

							#if the server status is up and the message type is declare the leader
							if ((global_info.getServerStatus() == MessageType.SERVERUP or global_info.getServerStatus() == MessageType.RUNNING) and message_type == MessageType.DECLARETHELEADER):
								print("global_info.getServerStatus()", global_info.getServerStatus(), "message type", message_type, " content", message_content)
								arrmessagecontent = message_content.split("#")
								theleaderport = int(arrmessagecontent[0])
								leaderstatus = arrmessagecontent[1]

								#deactivate the leader and or remove the leader
								if (leaderstatus == MessageContent.ACTIVE):
									deactivateTheLeader()
								else:
									removeTheLeader()

								#if it's my ip address and my port, then set I am the leader
								if (theleaderport == this_server.port):
									this_server.activateTheRoleAsTheLeader()
								else:
									theleader = getExisitngServerByPort(theleaderport)
									theleader.activateTheRoleAsTheLeader()

								updateSenderLastSendingMessageDateTime(sender_port, message_datetime)
								#set the params of global info
								global_info.setServerStatus(MessageType.RUNNING)
								global_info.setCurrentLeader(theleaderport)
								print("Voting done. My current global info is: server status:%s and the leader is %s"%(global_info.serverstatus,str(global_info.getCurrentLeader())))


							if (global_info.getServerStatus() == MessageType.RUNNING and message_type == MessageType.REQUESTLISTOFSERVER):
								print("I got message from %s with message type %s"%(str(sender_port),message_type))
								#announce the list of servers
								print("I will send the list of existing servers to %s"%(str(sender_port)))
								unicastMessage(this_server, MessageType.LISTOFEXISTINGSERVERS, getStrListOfConnectedServers(), getCurrentServerDateTime(), getExisitngServerByPort(sender_port).getAddress())

							#if slave goes down and my status is running
							if (global_info.getServerStatus() == MessageType.RUNNING and message_type == MessageType.SLAVEDOWN):
								print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
								#update my server list
								unavailable_server = getExisitngServerByPort(int(message_content))
								if (unavailable_server is not None):
									#update the unvaialable server status to inactive
									unavailable_server.deactivateServer()
								print("I have updated my server list.")
								showConnectedServers(this_server)

							#if there is an announcement of the new leader and my status is running
							if (global_info.getServerStatus() == MessageType.RUNNING and message_type == MessageType.ANNOUNCELEADER):
								print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))
								theleader = int(message_content)

								#remove the previous leader
								removeTheLeader()

								#get server by port
								theleader = getExisitngServerByPort(theleader)
								if (theleader is not None):
									#activate the role of the server as the leader
									theleader.activateTheRoleAsTheLeader()
									#set the params of global info
									global_info.setServerStatus(MessageType.RUNNING)
									global_info.setCurrentLeader(int(message_content))

								#update the last sending message datetime of the sender
								updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)
								print("This is my current global info:%s, current leader:%s"%(global_info.getServerStatus(), str(global_info.getCurrentLeader())))

							#if voting is launched and my status is running
							if (global_info.getServerStatus() == MessageType.RUNNING and message_type == MessageType.VOTING):
								print("I got message from %s with message type %s and the content is %s"%(str(sender_id[1]),message_type, message_content))

								#if the leader has been changed
								if (int(message_content) == global_info.getCurrentLeader()):
									#set my status to voting
									global_info.setServerStatus(MessageType.VOTING)

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
										print("I'm the leader now since I have the highest port over the others")
								else:
									#send the current leader to the sender
									unicastMessage(this_server, MessageType.ANNOUNCELEADER, str(global_info.getCurrentLeader()), getCurrentServerDateTime(), received_address)

								#update the last sending message datetime of the sender
								updateSenderLastSendingMessageDateTime(sender_id[1], message_datetime)

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

						if (global_info.getServerStatus() == MessageType.SERVERUP and message_type == MessageType.ACKNOWLEDGEMENTFROMALIVESERVER):
								print("I got message from %s with message type %s and the content is %s"%(sender_id[1],message_type, message_content))
								#update server status
								global_info.setServerStatus(MessageType.ACKNOWLEDGEMENTFROMALIVESERVER)
								#request list of server
								print("I request list of the servers to the group. My global status is %s"%(global_info.getServerStatus()))
								this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.REQUESTLISTOFSERVER, '', getCurrentServerDateTime()), this_server.getDiscoveryAddress())


						if (global_info.getServerStatus() == MessageType.ACKNOWLEDGEMENTFROMALIVESERVER and message_type == MessageType.LISTOFEXISTINGSERVERS):
								print("I got message from %s with message type %s and the content is %s"%(sender_id[1],message_type, message_content))
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
								updateSenderLastSendingMessageDateTime(int(sender_id[1]), message_datetime)
								#show current list of servers
								showConnectedServers(this_server)
								print("List of servers has been updated")
								#update my global info
								global_info.setServerStatus(MessageType.LISTOFSERVERUPDATED)


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
			if (isabletopingtheleader and this_server.isTheLeader() == False):
				print("**************** ping the leader %s *******************"%(str(global_info.getCurrentLeader())))
				unicastMessage(this_server, MessageType.PINGTHELEADER, '', getCurrentServerDateTime(), getTheLeader().getAddress())
				#deactivate isabletopingleader
				isabletopingtheleader = False
				#set sleeping time to 10
				sleep(2)
				#activate again isabletopingleader
				isabletopingtheleader = True

def thread_launch_election():
	global checktheleader
	while True:
		try:
			#if I am not the leader and the servers are running normally
			if (this_server.isTheLeader() == False and getTheLeader() is not None and global_info.getServerStatus() == MessageType.RUNNING and len(list_of_servers) > 1 and checktheleader == True):
				checktheleader = False
				first_theleaderlastdatetimesendingmessage = getTheLeader().getLastSendingMessageDateTime()
				first_delta = (MessageUtil.convertStringToDateTime(getCurrentServerDateTime()) - first_theleaderlastdatetimesendingmessage).total_seconds()
				print("**************** check whether the leader is alive *******************")
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
						servercrash = 1

						#if the members only one or my port is the highest among others then I'm the leader
						if (sorted_list_of_server_by_port[0].port == this_server.port):
							this_server.activateTheRoleAsTheLeader()
							global_info.setCurrentLeader(this_server.port)
							global_info.setServerStatus(MessageType.RUNNING)

							#announce that I'm the leader by sending message to multicast group
							this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.DECLARETHELEADER, str(this_server.port)+"#"+str(servercrash), getCurrentServerDateTime()), this_server.getDiscoveryAddress())
							print("I am the leader now and this is my global info:%s , %s"%(global_info.getServerStatus(), str(global_info.getCurrentLeader())))
						#launch election to the servers who have the higher port than me
						else:
							#if my status still pause running and other servers don't send anything yet, then I'll launch the election
							if (global_info.getServerStatus() == MessageType.PAUSERUNNING):
								#set server status and global status
								global_info.setServerStatus(MessageType.VOTING)

								print("Launching election")
								#announce that I'm the leader by sending message to multicast group
								this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.VOTING, str(global_info.getCurrentLeader()), getCurrentServerDateTime()), this_server.getDiscoveryAddress())

								#wait for 15 seconds
								#if there is not any reply after 15 seconds, then set the highest port to be the leader
								lst_active_servers = getActiveServers()
								sorted_list_of_server_by_port = sorted(lst_active_servers, key=lambda x: x.port, reverse=True)
								global_info.setCurrentLeader(sorted_list_of_server_by_port[0].port)
								global_info.setServerStatus(MessageType.RUNNING)

								#announce the highest port as the leader by sending message to multicast group
								this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.DECLARETHELEADER, str(sorted_list_of_server_by_port[0].port)+"#"+str(servercrash), getCurrentServerDateTime()), this_server.getDiscoveryAddress())

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

		#sleep for another 15 seconds
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
