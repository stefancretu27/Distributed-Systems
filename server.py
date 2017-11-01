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
import traceback
import types
#used for threads
from threading import Thread, Lock
from time import sleep
#import classes
from UDPServerModel import UDPServerModel
from DataPacketModel import DataPacketModel
from ClientModel import ClientModel
from MessageUtil import MessageUtil
from Enum import MessageType,SenderType,ConstantValues,MessageContent,KnownMessageID
from MessageHistoryModel import MessageHistoryModel
from GlobalInfo import GlobalInfo

#global lists
#store the info about the servers. It includes all servers (also self)
list_of_servers = list()
#store all connected clients in a list = client group view	
list_of_clients = list()
#store all crashed potential servers
list_of_crashed_potential_servers = list()

def compareOrderedLists(l1, l2):
	return l1==l2

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
			print ("   ",(server.ip, server.port),"joiningdatetime: ", server.getJoiningDateTime(), " lastsendingmessagedatetime:",server.getLastSendingMessageDateTime(),"is the leader:", server.isTheLeader())
	else:
		print ('[Server update] No other servers are currently connected to this server:', self.ip)

def getConnectedServersAddresses():
	if list_of_servers:
		return [server.getAddress() for server in list_of_servers if server.default == 0]
	else:
		return []

def multicastMessageToServers(message_id, message_type, message_content, message_datetime):
	#check if the list is not empty
	if list_of_servers:
		this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, message_id, message_type, message_content, message_datetime), \
		this_server.getDiscoveryAddress())

#used to send message to one entity server/client
def unicastMessage(message_id, message_type, message_content, message_datetime, target_address):
	this_server.socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, message_id, message_type, message_content, message_datetime), target_address)

def getStrListOfConnectedServers():
	strserver = ""
	lst_size = len(list_of_servers)
	idx = 0
	if lst_size > 0:
		for sv in list_of_servers:
			is_server_leader = 0
			if (sv.isTheLeader()):
				is_server_leader = 1

			if(idx == lst_size-1):
				strserver = strserver + str(sv.port)+"#"+MessageUtil.convertDateTimeToString(sv.getJoiningDateTime())+"#"+MessageUtil.convertDateTimeToString(sv.getLastSendingMessageDateTime())+"#"+str(is_server_leader)
			else:
				strserver = strserver + str(sv.port)+"#"+MessageUtil.convertDateTimeToString(sv.getJoiningDateTime())+"#"+MessageUtil.convertDateTimeToString(sv.getLastSendingMessageDateTime())+"#"+str(is_server_leader)+";"
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


def getTheLeaderFromServerList():
	theleader = None
	for server_item in list_of_servers:
		if (server_item.isTheLeader()):
			theleader = server_item
			break
	return theleader

def getServerByPort(_port):
	single_server = None
	for server_item in list_of_servers:
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
	# print ("[Server update] deactivate the old leader")
	for i, server in enumerate(list_of_servers):
		if server.port == global_info.getCurrentLeader():
			list_of_servers[i].deactivateTheRoleAsTheLeader()
			break

#useful when a server crashed and it sent an acknowledgement, but not all servers sent an acknowledgement
def removeDeadServerFromPacketsListOfReceivers(serverport):
	global global_lock
	if this_server.sending_messages_queue:
		global_lock.acquire()
		try:
			#if a packet still waits to be sent and one of its receivers crashed but sent ack
			for packet in this_server.sending_messages_queue:
				if serverport in packet.list_of_receivers:
					packet.list_of_receivers.remove(serverport)
		except:
			e = sys.exc_info()[0]
			print("[Server update] removeDeadServerFromPacketsListOfReceivers", e)
		finally:
			global_lock.release()

def isTheLeaderAlive():
	istheleaderalive = False
	theleader = getTheLeader()
	if (theleader is not None):
		if (theleader.port in getLitsOfServerPorts()):
			istheleaderalive = True

	return istheleaderalive


def removeTheLeader():
	# print ("[Server update] removing the old leader")
	try:
		# leader_port = None
		for i, server in enumerate(list_of_servers):
			if server.port == global_info.getCurrentLeader():
				# leader_port = server.port
				del list_of_servers[i]
				removeDeadServerFromPacketsListOfReceivers(server.port)
				break
				
		# if (leader_port is not None):

	except:
		e = sys.exc_info()[0]
		print("[Server update] Exception removing the server", e)

def removeTheServer(serverport):
	# print ("[Server update] removing the server")
	try:
		for i, server in enumerate(list_of_servers):
			if server.port == serverport:
				del list_of_servers[i]
				removeDeadServerFromPacketsListOfReceivers(serverport)
				break

	except:
		e = sys.exc_info()[0]
		print("[Server update] Exception removing the server", e)

def resetLastSendingMessageDateTimeAllServers():
	for server_item in list_of_servers:
		server_item.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(getCurrentServerDateTime()))

def updateSenderLastSendingMessageDateTime(_port, _lastsendingmessagedatetime):
	if (len(list_of_servers) > 1):
		sender_server = getServerByPort(_port)
		if (sender_server is not None):
			sender_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(_lastsendingmessagedatetime))

#list of clients related operations
#for various reasons a client will disconnect => update the list of clients
def disconnectClient(this_client):
	if list_of_clients:
		return [client for client in list_of_clients if client != this_client]
	else:
		return []
#display the port and ip of all clients
def showConnectedClients():
	if list_of_clients:
		for client in list_of_clients:
			print ("client adrress: ",(client.address), "server adrress:",client.server_address)
	else:
		print ('[Client update] Currently, no clients are connected in the system')
#search if a client is connected
def isClientInList(this_client):
	for client in list_of_clients:
		if client == this_client:
			return True
	return False

#send a message to all connected clients but to the one that sent it
def multicastMessagetoClients(this_client, message_type, serverdatetime):
#set message's parameters
	#message received from a clien and multicasted to the other clients
	multicast_sendertype = SenderType.CLIENT
	#the sender client is identified based on its ip and port, taken from address
	multicast_senderid = "%s:%s"%(this_client.address[0], this_client.address[1])
	#message content is not altered
	multicast_message = this_client.message
	multicast_datetime = serverdatetime

	#if a client joins or leaves
	if (message_type == MessageType.LEFTROOM or message_type == MessageType.JOINROOM):
		#create notifications
		if (message_type == MessageType.JOINROOM):
			multicast_message = '************************ client %s:%s joined the room ********************************' %(this_client.address[0],this_client.address[1])
		else:
			multicast_message = '************************ client %s:%s left the room ****************************' %(this_client.address[0],this_client.address[1])
		#the server sends notifications to all connected clients
		multicast_sendertype = SenderType.SERVER
		#specify the identity of the server that handles the join/leave operation
		multicast_senderid = "%s:%s"%(this_server.ip, this_server.port)

	#multicast the message
	for client in list_of_clients:

		#send message to only my clients
		# print("multicastMessagetoClients: client server address", client.server_address[1], "my port:",this_server.port)
		if (client.server_address[1] == this_server.port):
			if (client == this_client):
				if (message_type == MessageType.JOINROOM):
					this_server.socket.sendto(MessageUtil.constructMessage(multicast_senderid, multicast_sendertype, KnownMessageID.ClientMsg, MessageType.ACKNOWLEDGEFROMSERVER, \
												this_client.getJoiningDateTime(), multicast_datetime), client.address)
			else:
				this_server.socket.sendto(MessageUtil.constructMessage(multicast_senderid, multicast_sendertype, KnownMessageID.ClientMsg, message_type, multicast_message, multicast_datetime), \
											client.address)

def getConnectedClientsAddresses():
	if list_of_clients:
		return [client.getAddress() for client in list_of_clients]
	else:
		return []

def isClientExist(ip,port):
	exist = False
	for client_item in list_of_clients:
		if (client_item.address[0] == ip and client_item.address[1] == port):
			exist = True
			break
	return exist

def getExistingClientByAddress(ip,port):
	client = None
	for client_item in list_of_clients:
		if (client_item.address[0] == ip and client_item.address[1] == port):
			client = client_item
			break
	return client

def getExistingClientByPort(port):
	client = None
	for client_item in list_of_clients:
		if (client_item.address[1] == port):
			client = client_item
			break
	return client

def getStrListOfConnectedClients():
	strclient = ""
	lst_size = len(list_of_clients)
	idx = 0
	if lst_size > 0:
		for cl in list_of_clients:
			temp_joiningdatetime = MessageContent.NONE
			temp_leavingdatetime = MessageContent.NONE
			temp_messagedatetime = MessageContent.NONE

			if (cl.joiningdatetime is not None):
				temp_joiningdatetime = cl.joiningdatetime
			if (cl.leavingdatetime is not None):
				temp_leavingdatetime = cl.leavingdatetime
			if (cl.messagedatetime is not None):
				temp_messagedatetime = cl.messagedatetime

			if(idx == lst_size-1):
				strclient = strclient + str(cl.address[0])+"#" + str(cl.address[1])+"#"+temp_joiningdatetime+"#"+temp_leavingdatetime+"#"+temp_messagedatetime+"#"+str(cl.server_address[1])
			else:
				strclient = strclient + str(cl.address[0])+"#" + str(cl.address[1])+"#"+temp_joiningdatetime+"#"+temp_leavingdatetime+"#"+temp_messagedatetime+"#"+str(cl.server_address[1])+";"
			idx = idx+1
	return strclient

def updateClientsOfCrashedServer(port,newport):
	print("[Server update] The clients of crashed server: ", port, " (if any) are being moved to server ", newport)
	for client in list_of_clients:
		if client.server_address[1] == port:
			client.setServerAddress(newport)
	showConnectedClients()

isabletopingtheleader = True
checktheleader = True
alreadysentmessage = False

#store the info about the servers. It includes all servers (also self)
list_of_servers = list()

#store all connected clients in a list = client group view
list_of_clients = list()

#create global info
global_info = GlobalInfo()

#set message buffer size
message_buffer_size = 2048
localhost = '127.0.0.1'
sent_message_id = 0

#set list of message history
lst_messagehistory = []

#create server instance, on localhost, to handle client data exchange (with client, but also with servers)
this_server = UDPServerModel(localhost, int (sys.argv[1]))
#append server joining time and last sending message time
this_server.setJoiningDateTime(MessageUtil.convertStringToDateTime(getCurrentServerDateTime()))
#set global info status
global_info.setServerStatus(MessageType.SERVERUP)
#for this server instance, initialize the discovery socket
this_server.initializeDiscoverySocket()
#open server general socket
this_server.openSocket()
#append this_server instance to its own list of servers
list_of_servers.append(this_server)
#global lock for thread safe operations
global_lock = Lock()

#inform the admin that this server is up
print('[Server update] Server is starting up on %s port %s' % (this_server.ip, this_server.port))	

#global list of sockets used by multiple threads
socket_list = [this_server.socket, this_server.discovery_socket]

#set thread and timer
def thread_decidetheleader():
	global alreadysentmessage, isabletopingtheleader, checktheleader, sent_message_id, this_server, list_of_servers, global_info, global_lock
	#starting thread
	sleep(5)

	# condition.acquire()
	try:
		#set alreadysentmessage to false in to indicate that we're about to launch election. And we don't allow other servers to join
		alreadysentmessage = True

		#Decide the leader or the voting after 20 seconds
		if(global_info.getServerStatus() == MessageType.SERVERUP):
			#reset lastsendingmessagedatetime for all servers
			resetLastSendingMessageDateTimeAllServers()
			#sort servers by joining time and port
			sorted_list_of_server_by_joining_time = sorted(list_of_servers, key=lambda x: x.joiningdatetime, reverse=True)
			sorted_list_of_server_by_port = sorted(list_of_servers, key=lambda x: x.port, reverse=True)

			#if my joined times is greater than the others, then tell everyone that I will launch an election
			if(sorted_list_of_server_by_joining_time[len(sorted_list_of_server_by_joining_time)-1] == this_server):
				#launch the leader
				print("[Server update] Thread decide the leader is started")
				launchElection(this_server.port,MessageContent.SERVERALIVE)
				print("[Server update] Thread decide leader ended")

		if (global_info.getServerStatus() in [MessageType.LISTOFCLIENTSUPDATED]):
			print("global_info.getServerStatus()", global_info.getServerStatus())

			#get the leader from server list
			theleader = getTheLeaderFromServerList()
			sorted_list_of_server_by_port = sorted(list_of_servers, key=lambda x: x.port, reverse=True)

			if ((theleader is None and this_server.port == sorted_list_of_server_by_port[0].port) or (theleader is not None and this_server.port > theleader.port)):
				#if the leader exist, deactivate its role
				if (theleader is not None):
					theleader.deactivateTheRoleAsTheLeader()

				theleader = this_server
				print("[Server update] I am the leader now, and I will announce the message to everyone", this_server.port)
				#tell everyone that I am the leader
				voting_packet = DataPacketModel(getCurrentServerDateTime())
				sent_message_id += 2
				temp_msg_content = str(sorted_list_of_server_by_port[0].port)+"#"+MessageContent.SERVERALIVE
				voting_packet.buildPacket("voting", SenderType.SERVER, sent_message_id, MessageType.DECLARETHELEADER, temp_msg_content, voting_packet.receivedDateTime, this_server.port)
				
				global_lock.acquire()
				this_server.sending_messages_queue.append(voting_packet)
				global_lock.release()
			else:
				print("[Server update] I don't have a chance to be the leader. So, I will update my leader with the existing one : %s"%(str(theleader.port)))

			#update my status to running and set I'm the leader
			theleader.activateTheRoleAsTheLeader()
			global_info.setServerStatus(MessageType.RUNNING)
			global_info.setCurrentLeader(theleader.port)
	except:
		e = sys.exc_info()[0]
		print("[Server update] Do not worry, it is going to be fine", e)
	finally:
		print("[Server update] The leader: " + str(global_info.getCurrentLeader()) + " server status: " + str(global_info.getServerStatus()) + ", am i the leader? " + str(this_server.isTheLeader()) )

def thread_mainprocess():
	global alreadysentmessage, sent_message_id, this_server, list_of_servers, list_of_clients, global_info, global_lock 

	while True:
		read_sockets, write_sockets, error_sockets = select.select([], socket_list, [])
		#firstly, announce the others in the multicast group about this instance's existence sending port (argv[1]) as data
		for socket in write_sockets:
			if socket == this_server.discovery_socket:
				#multicast to group if server status is SERVERUP or my role is the leader
				if (socket == this_server.discovery_socket and (global_info.getServerStatus() == MessageType.SERVERUP or global_info.getServerStatus() == MessageType.SERVERBUSY) and \
				alreadysentmessage == False):
					message_datetime = getCurrentServerDateTime()
					this_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(message_datetime))
					#send message with this server's id, specifying that comes from a server entity, that the server is up and giving the port as message
					###the message is sent continuously, by each running server
					multicastMessageToServers(KnownMessageID.ServerUp, MessageType.SERVERUP, MessageUtil.convertDateTimeToString(this_server.getJoiningDateTime()), message_datetime)

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
					
				#don't append own message to the list of received messages
				if this_server.port != temp_packet.sender_id:
					#treat heartbeats differently, as they don't need to be sorted in the message_buffer
					if(temp_packet.message_type != MessageType.HEARTBEAT):
						#add packet in message queues, if it has not been received yet
						if temp_packet not in this_server.received_messages_queue:
							#append packet in the server's message log
							this_server.received_messages_queue.append(temp_packet)
							#append packet in the server's packets buffer used for processing messages
							this_server.message_buffer.append(temp_packet)
					else:
						this_server.recv_heartbeats_buffer.append(temp_packet)
				#but mark it as receieved by self by appending this_server instance to the list of receivers for the considered packet
				else:
					#sort list of servers in ascending order based on port id
					list_of_servers.sort(key=lambda server: server.port)
					#if there are still messages waiting to be sent and if the received message is not an own "SERVERUP"
					if temp_packet.message_type != MessageType.SERVERUP:
						for packet in this_server.sending_messages_queue:
							if packet == temp_packet and this_server not in packet.list_of_receivers:
								packet.list_of_receivers.append(this_server)

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
						#append packet in the server's message log
						this_server.received_messages_queue.append(temp_packet)
						#append packet in the server's packets buffer used for processing messages
						this_server.message_buffer.append(temp_packet)

		#process heartbeats, if any
		if this_server.recv_heartbeats_buffer:
			for packet in this_server.recv_heartbeats_buffer:
				#if server sent its heartbeat
				if ((global_info.getServerStatus() in [MessageType.RUNNING, MessageType.VOTING]) and packet.message_type == MessageType.HEARTBEAT):
					# print("I got message from %s with message type %s and the content is %s"%(str(packet.sender_id),packet.message_type, packet.message_content))
					#update the last sending message datetime of the sender
					updateSenderLastSendingMessageDateTime(packet.sender_id, packet.receivedDateTime)
				#remove packet
				this_server.recv_heartbeats_buffer.remove(packet)
			

		#once packets were read from sockets and appended to this_server message queue, the message queue is sorted based on sendingDateTime
		#this_server.received_messages_queue.sort(key=lambda packet: packet.sendingDateTime)
		this_server.message_buffer.sort(key=lambda packet: packet.sendingDateTime)
		
		#process received packets
		for packet in this_server.message_buffer:
			#if a packet was sent by a server
			if(packet.sender_type == SenderType.SERVER):
				#create a temporary server model with the received attributes
				temp_server = UDPServerModel(localhost, temp_packet.sender_id)
				#this server records the time of the last received packet from any servers connected in the multicast group. Actually, it is the time the packet was sent
				temp_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(str(packet.sendingDateTime)))
				
				#For each received message, that is not acknowledgement, inform the sender server that its message was received \
				#by building a similar packet (same message id and content, same sender type, same sending time) but with mesage type = RECEIVEDMESAGE. \
				#Then, it is unicasted to the sender, which makes the sending message queue to look like a sequence of acknowledgement and sending messages (ack, sm, ack, sm etc.)
				if(packet.message_type != MessageType.RECEIVEDMESSAGE and packet.message_type != MessageType.SERVERUP):
					#set time when ack message is issued
					sending_packet = DataPacketModel(getCurrentServerDateTime())
					sending_packet.buildPacket(temp_server.getAddress(), SenderType.SERVER, packet.message_id + 1, MessageType.RECEIVEDMESSAGE, packet.message_content, packet.sendingDateTime,\
					 this_server.port)
					
					global_lock.acquire()
					this_server.sending_messages_queue.append(sending_packet)
					global_lock.release()
				
				#Handle acknowledgements from other servers. 
				if(packet.message_type == MessageType.RECEIVEDMESSAGE):
					if isinstance(packet.message_content, list):
						packet.message_content[0] = unicodedata.normalize('NFKD', packet.message_content[0]).encode('ascii','ignore')
						packet.message_content = (packet.message_content[0], packet.message_content[1])
					#identify the packet in sending message queue for which the acknowledgement was received and add its sender it to list of receivers of the afferent message
					for pkt in this_server.sending_messages_queue:
						if pkt.message_type != MessageType.RECEIVEDMESSAGE and pkt.message_id == packet.message_id - 1 and pkt.sender_type == packet.sender_type and \
						pkt.sendingDateTime == packet.sendingDateTime and pkt.message_content == packet.message_content:
							receiver = UDPServerModel(localhost, packet.sender_id)
							pkt.list_of_receivers.append(receiver)
				
				if ((global_info.getServerStatus() in [MessageType.SERVERUP, MessageType.RUNNING, MessageType.REQUESTLISTOFSERVER, MessageType.ACKNOWLEDGEMENTFROMALIVESERVER, \
				MessageType.LISTOFCLIENTSUPDATED]) and packet.message_type  == MessageType.SERVERUP):
					#create a temporary server model with the received attributes
					temp_server = UDPServerModel(localhost, packet.sender_id)
					serverdatetime_received_acknowledgement = getCurrentServerDateTime()
					temp_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(packet.receivedDateTime))

					if temp_server.port not in getLitsOfServerPorts():
						temp_server.setJoiningDateTime(MessageUtil.convertStringToDateTime(packet.message_content))
						list_of_servers.append(temp_server)
						print ('[Server update] A new server is up. It runs on the address:%s. My global status is %s'%(str(temp_server.getAddress()), global_info.getServerStatus()))
						print ('[Server update] The current running servers are:')
						showConnectedServers()
						
						if (global_info.getServerStatus() == MessageType.RUNNING):
							#send acknowledgement to the newly added server
							print("[Server update] I send acknowledgement message to the newly added server, that is:", temp_server.port)
							unicastMessage(KnownMessageID.AckToNewServer, MessageType.ACKNOWLEDGEMENTFROMALIVESERVER, 'ack from alive server', packet.receivedDateTime, temp_server.getAddress())
							
				#if a new server wants to connect during the election, then send the message to try again in a few moments
				if (packet.message_type == MessageType.SERVERUP and (global_info.getServerStatus() in [MessageType.VOTING])):
					#if the sender is not on my server list, then refuse to connect
					if (packet.sender_id not in getLitsOfServerPorts()):
						unicastMessage(KnownMessageID.ServerBusy, MessageType.SERVERBUSY, 'server busy', packet.receivedDateTime, temp_server.getAddress())
					
				#if the server status is up and the message type is declare the leader
				if ((global_info.getServerStatus() in [MessageType.RUNNING, MessageType.SERVERUP, MessageType.VOTING]) and packet.message_type == MessageType.DECLARETHELEADER):
					#print("global_info.getServerStatus()", global_info.getServerStatus(), "message type", packet.message_type, " content", packet.message_content)
					arrmessagecontent = packet.message_content.split("#")
					theleaderport = int(arrmessagecontent[0])
					leaderstatus = arrmessagecontent[1]

					print("[Server update] Total active servers in the multicast group: ",len(list_of_servers))

					if ((global_info.getServerStatus() == MessageType.SERVERUP and len(list_of_servers)> 1)
						or global_info.getServerStatus() in [MessageType.RUNNING, MessageType.VOTING]):

						#deactivate the leader and or remove the leader
						if (leaderstatus == MessageContent.SERVERALIVE):
							deactivateTheLeader()
						else:
							#update server adrress of clients of the previous leader
							updateClientsOfCrashedServer(global_info.getCurrentLeader(),theleaderport)
							#update the server address of clients whose server address do not exist
							updateClientsOfCrashedServer(MessageContent.SERVERDOESNOTEXIST, theleaderport)
							removeTheLeader()

						#if it's my port, then set I am the leader
						if (theleaderport == this_server.port):
							this_server.activateTheRoleAsTheLeader()
						else:
							theleader = getExisitngServerByPort(theleaderport)
							#activate the corresponding server as the leader
							if (theleader is not None):
								theleader.activateTheRoleAsTheLeader()
							else:
								print("\n[Server update] I can't find the leader on my list of servers")

						updateSenderLastSendingMessageDateTime(packet.sender_id, packet.receivedDateTime)
						#set the params of global info
						global_info.setCurrentLeader(theleaderport)
						global_info.setServerStatus(MessageType.RUNNING)
						print("[Server update] Voting done. My current global info is: server status:%s and the leader is %s"%(global_info.serverstatus,str(global_info.getCurrentLeader())))

					
				if (global_info.getServerStatus() == MessageType.RUNNING and packet.message_type == MessageType.REQUESTLISTOFSERVER):
					print("[Server update] I got message from %s with message type %s"%(str(packet.sender_id), packet.message_type))
					#announce the list of servers
					print("[Server update] I will send the list of existing servers to %s"%(str(packet.sender_id)))
					unicastMessage(KnownMessageID.SendListofServers, MessageType.LISTOFEXISTINGSERVERS, getStrListOfConnectedServers(), getCurrentServerDateTime(), \
									getExisitngServerByPort(packet.sender_id).getAddress())


				if (global_info.getServerStatus() == MessageType.RUNNING and packet.message_type == MessageType.REQUESTLISTOFCLIENTS):
					#print("I got message from %s with message type %s"%(str(packet.sender_id), packet.message_type))
					#announce the list of servers
					print("[Server update] I will send the list of existing clients (if any) to %s"%(str(packet.sender_id)))
					unicastMessage(KnownMessageID.SendListOfClient, MessageType.LISTOFEXISTINGCLIENTS, getStrListOfConnectedClients(), getCurrentServerDateTime(), \
										getExisitngServerByPort(packet.sender_id).getAddress())
						
				#if slave goes down and my status is running
				if ((global_info.getServerStatus() in [MessageType.RUNNING, MessageType.VOTING]) and packet.message_type == MessageType.SLAVEDOWN):
					print("[Server update] I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))
					#update the server adrress of clients whose their server crashed with the id of the sender (the leader)
					crashed_slave = int(packet.message_content)

					if (isTheLeaderAlive()):
						#update clients of crashed server
						updateClientsOfCrashedServer(int(packet.message_content),getTheLeader().port)
						#update the server address of clients whose server address do not exist
						updateClientsOfCrashedServer(MessageContent.SERVERDOESNOTEXIST, getTheLeader().port)

					if (global_info.getServerStatus() == MessageType.VOTING):
						#clients of the crashed slave will be updated with no server (-999)
						updateClientsOfCrashedServer(crashed_slave, MessageContent.SERVERDOESNOTEXIST)

					#update group view
					removeTheServer(crashed_slave)

					print("[Server update] I have updated my server list.")
					showConnectedServers()

				#if voting is launched and my status is running
				if ((global_info.getServerStatus() in [MessageType.RUNNING, MessageType.SERVERUP,MessageType.VOTING]) and packet.message_type == MessageType.VOTING):
					#if the sender is on my server list, then allow them to participate in election
					if (packet.sender_id in getLitsOfServerPorts()):
						print("[Server update] I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))
						arrmessagecontent = packet.message_content.split("#")
						theleaderport = int(arrmessagecontent[0])
						theleaderstatus = arrmessagecontent[1]

						#if the leader has been changed
						if (theleaderport == global_info.getCurrentLeader() or global_info.getServerStatus() == MessageType.SERVERUP):
							#set my status to voting
							global_info.setServerStatus(MessageType.VOTING)

							#remove the previous leader
							if (theleaderstatus ==MessageContent.SERVERCRASH):
								#also from the list of ack senders for all packets in sending_message_queue
								removeTheLeader()

							#sort the members by port
							sorted_list_of_server_by_port = sorted(list_of_servers, key=lambda x: x.port, reverse=True)

							#if the members only one or my port is the highest among others then I'm the leader
							if (sorted_list_of_server_by_port[0].port == this_server.port):
								this_server.activateTheRoleAsTheLeader()
								global_info.setCurrentLeader(this_server.port)

								#announce that I'm the leader by sending message to multicast group
								voting_packet = DataPacketModel(getCurrentServerDateTime())
								sent_message_id += 2
								temp_msg_content = str(this_server.port)+"#"+theleaderstatus
								voting_packet.buildPacket("voting", SenderType.SERVER, sent_message_id, MessageType.DECLARETHELEADER, temp_msg_content, voting_packet.receivedDateTime, this_server.port)
								
								global_lock.acquire()
								this_server.sending_messages_queue.append(voting_packet)
								global_lock.release()
								#change my status to running
								global_info.setServerStatus(MessageType.RUNNING)
								print("[Server update] I'm the leader now since I have the highest port over the others. I will multicast this message")


								if(theleaderstatus == MessageContent.SERVERCRASH):
									#send multicast message to all clients of the corresponding crashed server
									client_packet = DataPacketModel(getCurrentServerDateTime())
									sent_message_id += 2
									client_packet.buildPacket(MessageType.CLIENTANNOUNCEMENTSERVERDOWN, SenderType.SERVER, sent_message_id, MessageType.CLIENTANNOUNCEMENTSERVERDOWN, str(theleaderport)+"#"+str(this_server.port), \
										client_packet.receivedDateTime, this_server.port)
									global_lock.acquire()
									this_server.sending_messages_queue.append(client_packet)
									global_lock.release()

									#update clients of crashed server with my port
									updateClientsOfCrashedServer(theleaderport, this_server.port)
						else:
							#get server by port
							previousleader = getExisitngServerByPort(theleaderport)
							if (previousleader is None):
								#send the current leader to the sender
								print("[Server update] The leader has changed, the newest one is %s"%(str(global_info.getCurrentLeader())))
								unicastMessage(KnownMessageID.AnnounceLeader, MessageType.ANNOUNCELEADER, str(global_info.getCurrentLeader()), packet.receivedDateTime, (localhost, packet.sender_id))

						#update the last sending message datetime of the sender
						updateSenderLastSendingMessageDateTime(packet.sender_id, packet.receivedDateTime)

								#if there is an announcement of the new leader and my status is running
				if ((global_info.getServerStatus() in [MessageType.RUNNING, MessageType.VOTING]) and packet.message_type == MessageType.ANNOUNCELEADER):
					print("[Server update] I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))
					#get server by port
					theleaderport = int(packet.message_content)
					theleader = getExisitngServerByPort(theleaderport)

					if (theleader is not None):
						if (theleader.port != global_info.getCurrentLeader()):
							#update clients of crashed server with my port
							updateClientsOfCrashedServer(global_info.getCurrentLeader(), theleader.port)
							#update the server address of clients whose server address do not exist
							updateClientsOfCrashedServer(MessageContent.SERVERDOESNOTEXIST, theleader.port)
							#remove the previous leader
							removeTheLeader()

							#activate the role of the server as the leader
							theleader.activateTheRoleAsTheLeader()
							#set the params of global info
							global_info.setServerStatus(MessageType.RUNNING)
							global_info.setCurrentLeader(theleader.port)

					#update the last sending message datetime of the sender
					updateSenderLastSendingMessageDateTime(packet.sender_id, packet.receivedDateTime)
					print("[Server update] His is my current global info:%s, current leader:%s"%(global_info.getServerStatus(), str(global_info.getCurrentLeader())))
					
				if ((global_info.getServerStatus() in [MessageType.SERVERUP, MessageType.SERVERBUSY]) and packet.message_type == MessageType.ACKNOWLEDGEMENTFROMALIVESERVER):
					print("[Server update] I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))
					#update server status
					global_info.setServerStatus(MessageType.ACKNOWLEDGEMENTFROMALIVESERVER)
					#request list of server
					print("[Server update] I request list of the servers to the group. My global status is %s"%(global_info.getServerStatus()))
					multicastMessageToServers(KnownMessageID.RequestListofServers, MessageType.REQUESTLISTOFSERVER, "req list of servers", getCurrentServerDateTime())

				if (global_info.getServerStatus() == MessageType.SERVERUP and packet.message_type == MessageType.SERVERBUSY):
					#set already sent message to true
					alreadysentmessage = True
					print("[Server update]  Attention! Server is busy now, please try again in a few minutes")
					#update server status
					global_info.setServerStatus(MessageType.SERVERBUSY)
					#quit
					this_server.closeSocket()
					sys.exit(0)	
				
				if ( (global_info.getServerStatus() in [MessageType.ACKNOWLEDGEMENTFROMALIVESERVER]) and packet.message_type == MessageType.LISTOFEXISTINGSERVERS):
					print("[Server update] I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))
					arr_existing_servers = packet.message_content.split(";")
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

						#if server not in the list, then add
						if (item_server_port not in getLitsOfServerPorts()):
							list_of_servers.append(item_arr_server_obj)
						else:
							#get existing server and update the joiningdatetime and lastsendingmessagedatetime
							existing_server = getExisitngServerByPort(item_server_port)
							existing_server.setJoiningDateTime(item_server_joiningtime)
							existing_server.setLastSendingMessageDateTime(item_server_lastsendingmessage)

					#update the last sending message datetime of the sender
					updateSenderLastSendingMessageDateTime(packet.sender_id, packet.receivedDateTime)
					#show current list of servers
					showConnectedServers()
					print("[Server update] List of servers has been updated")
					#update my global info if my status is not running or voting
					global_info.setServerStatus(MessageType.REQUESTLISTOFCLIENTS)
					
					#request list of server
					print("I request list of the servers to the group. My global status is %s"%(global_info.getServerStatus()))
					multicastMessageToServers(KnownMessageID.RequestListofClients, MessageType.REQUESTLISTOFCLIENTS, "req list of clients", getCurrentServerDateTime())

				if ((global_info.getServerStatus() in [MessageType.REQUESTLISTOFCLIENTS]) and packet.message_type == MessageType.LISTOFEXISTINGCLIENTS):

					print("I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))

					#if the content is not blank
					if (packet.message_content != ""):
						arr_existing_clients = packet.message_content.split(";")
						print("length of array", len(arr_existing_clients))
						for item_arr in arr_existing_clients:
							item_clients_arr = item_arr.split("#")
							item_client_ip = item_clients_arr[0]
							item_client_port = int(item_clients_arr[1])
							item_client_joiningdatetime = item_clients_arr[2]
							item_client_leavingdatetime = item_clients_arr[3]
							item_client_lastsendingmessage = item_clients_arr[4]
							item_client_server_address_port = int(item_clients_arr[5])

							item_arr_client_obj = ClientModel('', (item_client_ip, item_client_port))
							item_arr_client_obj.setServerAddress(item_client_server_address_port)
							item_arr_client_obj.setJoiningDateTime(item_client_joiningdatetime)

							if (item_client_joiningdatetime != MessageContent.NONE):
								item_arr_client_obj.setJoiningDateTime(item_client_joiningdatetime)
							if (item_client_leavingdatetime != MessageContent.NONE):
								item_arr_client_obj.setLeavingDateTime(item_client_leavingdatetime)
							if (item_client_lastsendingmessage != MessageContent.NONE):
								item_arr_client_obj.setMessageDateTime(item_client_lastsendingmessage)

							#if client not in the list, then add
							if (isClientExist(item_client_ip,item_client_port) == False):
								list_of_clients.append(item_arr_client_obj)
							else:
								#get existing server and update the joiningdatetime and lastsendingmessagedatetime
								existing_client = getExistingClientByAddress(item_client_ip,item_client_port)
								existing_client.setServerAddress(item_client_server_address_port)
								existing_client.setJoiningDateTime(item_client_joiningdatetime)

								if (item_client_joiningdatetime != MessageContent.NONE):
									existing_client.setJoiningDateTime(item_client_joiningdatetime)
								if (item_client_leavingdatetime != MessageContent.NONE):
									existing_client.setLeavingDateTime(item_client_leavingdatetime)
								if (item_client_lastsendingmessage != MessageContent.NONE):
									existing_client.setMessageDateTime(item_client_lastsendingmessage)

						#show current list of servers
						showConnectedClients()
						print("[Server update] List of clients has been updated")

					#update the last sending message datetime of the sender
					updateSenderLastSendingMessageDateTime(packet.sender_id, packet.receivedDateTime)

					#update my global info
					global_info.setServerStatus(MessageType.LISTOFCLIENTSUPDATED)

				if (packet.message_type == MessageType.ACKNOWLEDGEMENTVOTING):
					print("[Server update] I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))
					global_info.setServerStatus(MessageType.ACKNOWLEDGEMENTVOTING)
					#update the last sending message datetime of the sender
					updateSenderLastSendingMessageDateTime(packet.sender_id, packet.receivedDateTime)
					
				if(packet.message_type == MessageType.REQUESTMISSINGMESSAGE):
					missing_message_id = int (packet.message_content)
					#search for message sent by self that matches with the received id
					for packet in this_server.sent_messages_queue:
						#if the message is found
						if packet.message_id == missing_message_id:
							#appending to the buffer queue to be resent
							this_server.sending_messages_queue.append(packet)

				#Server handles client related events
				#If a new client has connected to another server instance or if this_server joined later, it gets the attributes of the client(s) from the other servers	
				if(packet.message_type == MessageType.JOINROOM):
					new_client = None
					#If this_server joined later, it gets a list of more clients as message_content
					if all(isinstance(elem, list) for elem in packet.message_content):
						for client_address in packet.message_content:
						#Get each client's address = ip + port, that is received as list, not as tuple
							client_ip = unicodedata.normalize('NFKD', client_address[0]).encode('ascii','ignore')

							#Create a client object
							new_client = ClientModel('', (client_ip, client_address[1]))
							new_client.server_address = (localhost, packet.sender_id)
							#If the client is not in this_server's clients group view, add it (remove duplicate message tactic)
							if new_client not in list_of_clients:
								list_of_clients.append(new_client)

						#inform the admin
						print ('\n[Client update] There are ' + str(len(packet.message_content)) + ' client(s) connected in the system')

					else:
					#If this server is running and a new client joined on another running server, the message content is the new client's address = ip+port (received as list, not as tuple)
						if isinstance(packet.message_content, unicode):
							packet.message_content[0] = unicodedata.normalize('NFKD', packet.message_content[0]).encode('ascii','ignore')
							
						new_client = ClientModel('', (packet.message_content[0], packet.message_content[1]))
						new_client.server_address = (localhost, packet.sender_id)
						#Add the client in the list, but firstly check if it's there (remove duplicate message tactic)	
						if new_client not in list_of_clients:
							list_of_clients.append(new_client)
							
						#inform the admin		
						sender_id = packet.sender_id
						print ('\n[Client update] A new client has joined on server: '+ str(sender_id))
						print("client packet ", packet.message_content)

					#send messages to my clients
					#build a packet
					client_packet = DataPacketModel(getCurrentServerDateTime())
					client_packet.buildPacket(new_client, SenderType.CLIENT, -1, MessageType.JOINROOM, new_client.address, packet.receivedDateTime, this_server.port)
					#send message to the other connected clients
					this_server.sending_messages_queue.append(client_packet)
					
					#show to admin all connected clients	

					print ('\n[Client update] The currently connected clients in the system are:')

					showConnectedClients()
				
				if(packet.message_type == MessageType.LEFTROOM):
					#the message content is the new client's address = ip+port (received as list, not as tuple)
					msg_content = packet.message_content
					if isinstance(packet.message_content, unicode):
						msg_content[0] = unicodedata.normalize('NFKD', msg_content[0]).encode('ascii','ignore')
					old_client = ClientModel('', (msg_content[0], msg_content[1]))

					#build a packet
					client_packet = DataPacketModel(getCurrentServerDateTime())
					#send message to the other connected clients
					client_packet.buildPacket(old_client, SenderType.CLIENT, -1, MessageType.LEFTROOM, old_client.address, packet.receivedDateTime, this_server.port)

					global_lock.acquire()
					this_server.sending_messages_queue.append(client_packet)
					global_lock.release()

					#Remove this client from the list of clients
					list_of_clients = disconnectClient(old_client)
					#show results on server side
					print ('\n[Client update] Client ' + str(old_client.address) + ' has left. The current logged in clients are:')
					showConnectedClients()

				if(packet.message_type == MessageType.NORMALCHAT):
					#pending
					#print ("I received message from ",packet.sender_id, " content:", packet.message_content)
					arr_messagecontent = packet.message_content.split("#")
					client_port = int(arr_messagecontent[0])
					client_messagecontent = arr_messagecontent[1]

					sender_client = getExistingClientByPort(client_port)
					# #append the message to the message history list
					lst_messagehistory.append(MessageHistoryModel(client_messagecontent,packet.receivedDateTime,sender_client))
					#record message datetime
					sender_client.setMessageDateTime(packet.receivedDateTime)

					# #update his message in list, as only the last message matters. Also, the message was previously updated in the local variable existing_client
					for client in list_of_clients:
						if client.address[1] == sender_client.address[1]:
							client.setMessage(client_messagecontent)

					#build a packet
					client_packet = DataPacketModel(getCurrentServerDateTime())
					client_packet.buildPacket(sender_client, SenderType.CLIENT, -1, MessageType.NORMALCHAT, (localhost,client_port), packet.receivedDateTime, this_server.port)

					#send message to the other servers and connected clients
					global_lock.acquire()
					this_server.sending_messages_queue.append(client_packet)
					global_lock.release()

					
				#remove processed packet from the received_messages_queue
				this_server.message_buffer.remove(packet) 
	
			#handle communication with the clients
			if (packet.sender_type == SenderType.CLIENT):
				#Each time a message is received from a client, create a temporary client object with the received attributes(message + address)
				temp_client = ClientModel(packet.message_content, packet.sender_address)
				temp_client.server_address = (localhost, this_server.port)
				
				#process client's packet only when running
				if(global_info.getServerStatus() == MessageType.RUNNING):											
					#if a new client has joined the conversation
					if (packet.message_type == MessageType.JOINROOM):
						#record joining datetime
						temp_client.setJoiningDateTime(packet.receivedDateTime)
						#append the new client to the list
						list_of_clients.append(temp_client)

						#show the entire list of available connections
						print ('\n[Client update] A new client has joined on this server, using the address ' + str(temp_client.address) + '. The current logged in clients are:')
						for client in list_of_clients:
							print ("   ",(client.address), (client.server_address))

						#build a packet
						server_packet = DataPacketModel(getCurrentServerDateTime())
						#server_packet.list_of_receivers = list()
						sent_message_id += 2
						#send message to the other server instances to inform them that a new client has connected as they need to update their client group view
						server_packet.buildPacket("recv from client", SenderType.SERVER, sent_message_id, MessageType.JOINROOM, packet.sender_address, packet.receivedDateTime, this_server.port)
						
						#build a packet
						client_packet = DataPacketModel(getCurrentServerDateTime())
						#send message to the other connected clients
						client_packet.buildPacket(temp_client, SenderType.CLIENT, KnownMessageID.ClientMsg, MessageType.JOINROOM, packet.sender_address, packet.receivedDateTime, this_server.port)
						
						global_lock.acquire()
						this_server.sending_messages_queue.append(server_packet)
						this_server.sending_messages_queue.append(client_packet)
						global_lock.release()
						
					#If the client quit the chat, the client application sends a 'quit' message.
					if (packet.message_type == MessageType.LEFTROOM):
						#make sure the client attributes are in this_server's client group view
						if isClientInList(temp_client):
							#record leving datetime
							temp_client.setLeavingDateTime(temp_packet.receivedDateTime)
							
							#build a packet
							server_packet = DataPacketModel(getCurrentServerDateTime())
							#send message to the other server instances to inform them that a new client has left as they need to update their client group view
							sent_message_id += 2
							server_packet.buildPacket("recv from client", SenderType.SERVER, sent_message_id, MessageType.LEFTROOM, packet.sender_address, packet.receivedDateTime, this_server.port)
							
							#build a packet
							client_packet = DataPacketModel(getCurrentServerDateTime())
							#send message to the other connected clients
							client_packet.buildPacket(temp_client, SenderType.CLIENT, KnownMessageID.ClientMsg, MessageType.LEFTROOM, packet.sender_address, packet.receivedDateTime, this_server.port)
							
							global_lock.acquire()
							this_server.sending_messages_queue.append(server_packet)
							this_server.sending_messages_queue.append(client_packet)
							global_lock.release()
						
							#Remove this client from the list of clients
							list_of_clients = disconnectClient(temp_client)

							#show results on server side
							print ('\n[Client update] Client ' + str(temp_client.address) + ' has left. The current logged in clients are:')
							showConnectedClients()
					
					#If the client sent a message to the chat room
					if (packet.message_type == MessageType.NORMALCHAT):
						#make sure the client attributes are in this_server's client group view
						if isClientInList(temp_client):
							#append the message to the message history list
							lst_messagehistory.append(MessageHistoryModel(packet.message_content,packet.receivedDateTime,temp_client))
							#record message datetime
							temp_client.setMessageDateTime(packet.receivedDateTime)
							
							#update his message in list, as only the last message matters. Also, the message was previously updated in the local variable existing_client
							for client in list_of_clients:
								if client == temp_client:
									client.setMessage(temp_client.message)

							#build a packet
							server_packet = DataPacketModel(getCurrentServerDateTime())
							#send message to the other server instances to inform them that a new client has left as they need to update their client group view
							server_packet_message_content = str(packet.sender_address[1])+"#"+packet.message_content
							sent_message_id += 2
							server_packet.buildPacket("recv from client", SenderType.SERVER, sent_message_id, MessageType.NORMALCHAT, server_packet_message_content, packet.receivedDateTime, this_server.port)

							#build a packet
							client_packet = DataPacketModel(getCurrentServerDateTime())
							client_packet.buildPacket(temp_client, SenderType.CLIENT, KnownMessageID.ClientMsg, MessageType.NORMALCHAT, packet.sender_address, packet.receivedDateTime, this_server.port)

							global_lock.acquire()
							this_server.sending_messages_queue.append(server_packet)
							this_server.sending_messages_queue.append(client_packet)
							global_lock.release()
				
					#remove processed packet from the received_messages_queue
					this_server.message_buffer.remove(packet)	
				#inform the client server is busy and keep clients packet			
				else:
					client_packet = DataPacketModel(getCurrentServerDateTime())
					client_packet.buildPacket(temp_client, SenderType.CLIENT, KnownMessageID.ClientMsg, MessageType.SERVERBUSY, "server busy or temporarily unavailable", packet.receivedDateTime, this_server.port)
					#send message to the other connected clients
					global_lock.acquire()
					this_server.sending_messages_queue.append(client_packet)
					global_lock.release()
					
		
def thread_sending_message():
	global global_lock
	while True:
		global_lock.acquire()
		try:
			for packet in this_server.sending_messages_queue:
				#append the packet to sent_messages_queue for permanent storage
				this_server.sent_messages_queue.append(packet)
				
				if (packet.sender_type == SenderType.SERVER):
					if packet.metadata == "recv from client" or packet.metadata == "voting" or packet.metadata == MessageType.CLIENTANNOUNCEMENTSERVERDOWN:
						multicastMessageToServers(packet.message_id, packet.message_type, packet.message_content, packet.sendingDateTime)

						#if all servers in the group view received the message, removed the message from the list. Valid only for IP server multicast
						packet.list_of_receivers.sort(key=lambda server: server.port)
						if list_of_servers == packet.list_of_receivers:
							this_server.sending_messages_queue.remove(packet)

						#print "Servers", [server.port for server in list_of_servers]
						#print "Receivers", [server.port for server in packet.list_of_receivers]
					else:
						unicastMessage(packet.message_id, packet.message_type, packet.message_content, packet.sendingDateTime, packet.metadata)
						this_server.sending_messages_queue.remove(packet)

				if (packet.sender_type == SenderType.CLIENT):
					multicastMessagetoClients(packet.metadata, packet.message_type, packet.sendingDateTime)
					this_server.sending_messages_queue.remove(packet)

		except:
			# print("exception")
			e = sys.exc_info()[0]
		finally:
			global_lock.release()
		
isAbleToSendHeartBeat = True
def thread_sendheartbeat():
	global isAbleToSendHeartBeat
	while True:
		if (isAbleToSendHeartBeat):
			# print("====================== I send my heart beat=========================")
			multicastMessageToServers(KnownMessageID.HeartBeat,  MessageType.HEARTBEAT, "heartbeat", getCurrentServerDateTime())
			isAbleToSendHeartBeat = False
			#set sleeping time to 15 => send 4 HB per minute
			sleep(5)
			isAbleToSendHeartBeat = True


#check whether the server is alive
def thread_checkservers():
	while True:
		if (global_info.getServerStatus() == MessageType.RUNNING):
			#if I'm the slave, then I will check the leader
			if (this_server.isTheLeader() == False):
				#create new thread to check each server
				try:
					thread_server = Thread(target=thread_checkeachserver, args=(global_info.getCurrentLeader(),True,))
					thread_server.start()
					thread_server.join()
				except:
					e = sys.exc_info()[0]
					print("[Server update] Exception in thread check the leader", e)
			#if I'm the leader, then I will check all slaves
			else:
				for server in list_of_servers:
					if server.port != this_server.port:
						#create new thread to check each server
						try:
							thread_server = Thread(target=thread_checkeachserver, args=(server.port,False,))
							thread_server.start()
							thread_server.join()
						except:
							e = sys.exc_info()[0]
							print("[Server update] Exception in thread_checkservers", e)

#ping each server
def thread_checkeachserver(port,istheleader):
	global sent_message_id, this_server, list_of_servers, global_lock
	try:
		#get exisiting server
		existing_server = getExisitngServerByPort(port)
		if existing_server is not None:
			#print "1", port, existing_server.port
			#get the first delta of existing server
			first_datetimesendingmessage = existing_server.getLastSendingMessageDateTime()
			first_delta = (MessageUtil.convertStringToDateTime(getCurrentServerDateTime()) - first_datetimesendingmessage).total_seconds()

			#compare delta value with its maximum
			if (first_delta > ConstantValues.DELTAMAX):
				#wait for 20 seconds
				sleep(20)
				#get the second delta of existing server
				temp_server  = getExisitngServerByPort(port)
				if temp_server is not None:
					second_datetimesendingmessage = temp_server.getLastSendingMessageDateTime()
					second_delta = (MessageUtil.convertStringToDateTime(getCurrentServerDateTime()) - second_datetimesendingmessage).total_seconds()
					print("[Server update] Checking server status %s, second delta:%s"%(str(port),str(second_delta)))

					#again, compare delta value with its maximum threshold
					if (second_delta > ConstantValues.DELTAMAX):
						#get the existing server
						last_check_server = getExisitngServerByPort(port)

						if (last_check_server is not None):
							print "2", port, last_check_server.port
							if(istheleader):
								print("[Server update] I am checking the leader")
								#launch leader election
								launchElection(last_check_server.port, MessageContent.SERVERCRASH)

							else:
								#inform servers in multicast group that someone crash
								print("[Server update] I am checking the slaves")
								#leader removes the corresponding server from group view
								# list_of_servers_lock.acquire()
								removeTheServer(last_check_server.port)
								# list_of_servers_lock.release()

								#send multicast message to all other servers
								voting_packet = DataPacketModel(getCurrentServerDateTime())
								sent_message_id += 2
								temp_msg_content = str(last_check_server.port)
								voting_packet.buildPacket("voting", SenderType.SERVER, sent_message_id, MessageType.SLAVEDOWN, temp_msg_content, voting_packet.receivedDateTime, this_server.port)

								#send multicast message to all clients of the corresponding crashed server
								client_packet = DataPacketModel(getCurrentServerDateTime())
								sent_message_id += 2
								client_packet.buildPacket(MessageType.CLIENTANNOUNCEMENTSERVERDOWN, SenderType.SERVER, sent_message_id, MessageType.CLIENTANNOUNCEMENTSERVERDOWN, str(existing_server.port)+"#"+str(this_server.port), \
									client_packet.receivedDateTime, this_server.port)

								global_lock.acquire()
								this_server.sending_messages_queue.append(voting_packet)
								this_server.sending_messages_queue.append(client_packet)
								global_lock.release()

								#update clients of crashed server
								updateClientsOfCrashedServer(last_check_server.port, this_server.port)

								print("[Server update] server %s went down. The multicast message has been sent to the other servers to let them know which one crashed."%(str(port)))
								showConnectedServers()
	except:
		exc_info = sys.exc_info()
		print("[Server update] Exception in thread_checkeachserver. Do not worry, it's going to be fine :)")
		traceback.print_exception(*exc_info)

#method to launch an election
def launchElection(port,leaderstatus):
	global sent_message_id, global_lock,list_of_crashed_potential_servers
	try:
		if (leaderstatus == MessageContent.SERVERCRASH):
			print("[Server update] The leader %s crashed. Voting will be relaunched."%(str(port)))
			#remove the previous leader
			removeTheLeader()

		#sort the members by port
		sorted_list_of_server_by_port = sorted(list_of_servers, key=lambda x: x.port, reverse=True)

		#if the members only one or my port is the highest among others then I'm the leader
		if (sorted_list_of_server_by_port[0].port == this_server.port):
			this_server.activateTheRoleAsTheLeader()
			global_info.setCurrentLeader(this_server.port)

			#announce that I'm the leader by sending message to multicast group
			voting_packet = DataPacketModel(getCurrentServerDateTime())
			sent_message_id += 2
			temp_msg_content = str(this_server.port)+"#"+leaderstatus
			voting_packet.buildPacket("voting", SenderType.SERVER, sent_message_id, MessageType.DECLARETHELEADER, temp_msg_content, voting_packet.receivedDateTime, this_server.port)

			global_lock.acquire()
			this_server.sending_messages_queue.append(voting_packet)
			global_lock.release()
			#set global status to running
			global_info.setServerStatus(MessageType.RUNNING)
			print("[Server update] I am the leader now and this is my global info:%s , %s"%(global_info.getServerStatus(), str(global_info.getCurrentLeader())))


			if (leaderstatus == MessageContent.SERVERCRASH):
				#send multicast message to all clients of the corresponding crashed leader
				client_packet = DataPacketModel(getCurrentServerDateTime())
				sent_message_id += 2
				client_packet.buildPacket(MessageType.CLIENTANNOUNCEMENTSERVERDOWN, SenderType.SERVER, sent_message_id, MessageType.CLIENTANNOUNCEMENTSERVERDOWN, str(port)+"#"+str(this_server.port), \
					client_packet.receivedDateTime, this_server.port)
				global_lock.acquire()
				this_server.sending_messages_queue.append(client_packet)
				global_lock.release()

				#send multicast message to all clients of the corresponding crashed potential leaders
				for potential_leader in list_of_crashed_potential_servers:
					#send multicast message to all clients of the corresponding crashed leader
					client_packet = DataPacketModel(getCurrentServerDateTime())
					sent_message_id += 2
					client_packet.buildPacket(MessageType.CLIENTANNOUNCEMENTSERVERDOWN, SenderType.SERVER, sent_message_id, MessageType.CLIENTANNOUNCEMENTSERVERDOWN, str(potential_leader)+"#"+str(this_server.port), \
						client_packet.receivedDateTime, this_server.port)
					global_lock.acquire()
					this_server.sending_messages_queue.append(client_packet)
					global_lock.release()

				#empty the list of crashed potential server
				list_of_crashed_potential_servers = []

				#update clients of crashed server with my port
				updateClientsOfCrashedServer(port, this_server.port)
				#update the server address of clients of the corresponding crashed leader
				updateClientsOfCrashedServer(MessageContent.SERVERDOESNOTEXIST, this_server.port)

		#otherwise, launch election
		else:
			print("[Server update] Launching election")
			#announce that I'm the leader by sending message to multicast group
			voting_packet = DataPacketModel(getCurrentServerDateTime())
			sent_message_id += 2
			temp_msg_content = str(port)+"#"+leaderstatus
			voting_packet.buildPacket("voting", SenderType.SERVER, sent_message_id, MessageType.VOTING, temp_msg_content, voting_packet.receivedDateTime, this_server.port)
			
			global_lock.acquire()
			this_server.sending_messages_queue.append(voting_packet)
			global_lock.release()

			#set server status and global status
			global_info.setServerStatus(MessageType.VOTING)
			#wait for 20 seconds
			sleep(10)
			print("[Server update] My status after 20 seconds", global_info.getServerStatus(), " the leader:",global_info.getCurrentLeader())
			#if the status is still voting after 20 seconds, then
			if (global_info.getServerStatus() == MessageType.VOTING and (port == global_info.getCurrentLeader())):
				#sort the members by port
				sorted_list_of_server_by_port = sorted(list_of_servers, key=lambda x: x.port, reverse=True)

				#get the delta of each server
				for server in sorted_list_of_server_by_port:
					if server.port != this_server.port :
						if (global_info.getServerStatus() == MessageType.VOTING and isTheLeaderAlive() == False):
							server_datetimesendingmessage = server.getLastSendingMessageDateTime()
							server_delta = (MessageUtil.convertStringToDateTime(getCurrentServerDateTime()) - server_datetimesendingmessage).total_seconds()
							#if server delta greater than maximum treshold
							if (server_delta > ConstantValues.DELTAMAX):
								#store crashed potential server into a list
								list_of_crashed_potential_servers.append(server.port)
								#remove the corresponding server
								removeTheServer(server.port)

								#clients of the crashed server will be updated with no server (-999)
								updateClientsOfCrashedServer(server.port, MessageContent.SERVERDOESNOTEXIST)

								#send multicast message to all other servers
								voting_packet = DataPacketModel(getCurrentServerDateTime())
								sent_message_id += 2
								temp_msg_content = str(server.port)
								voting_packet.buildPacket("voting", SenderType.SERVER, sent_message_id, MessageType.SLAVEDOWN, temp_msg_content, voting_packet.receivedDateTime, this_server.port)

								global_lock.acquire()
								if (global_info.getServerStatus() == MessageType.VOTING):
									this_server.sending_messages_queue.append(voting_packet)
									print("[Server update] server %s is going down. The multicast message has been sent to the other servers"%(str(server.port)))
								global_lock.release()


								#Then re-launch the election
								sleep(5)
								if (global_info.getServerStatus() == MessageType.VOTING and isTheLeaderAlive() == False):
									print("[Server update] Relaunch the election because someone has just crashed")
									launchElection(global_info.getCurrentLeader(), MessageContent.SERVERCRASH)

								break
			showConnectedServers()
	except:
		print("[Server update] Do not worry, it is going to be fine")

def thread_check_missing_packets():
	print("[Server update] Started to search for eventually missing packets")
	#list of messages to be checked
	packets_to_be_checked = list()
	
	#take all packets that need to be checked (even positive message IDs)
	#it also filters the received packets, so sorting works with fewer packets
	for packet in this_server.received_messages_queue:
		#don't check unicasted messages (negative IDs), ServerUP (0) and acknowledgements (odd ids)
		if packet.message_id > 0 and packet.message_id%2 == 0:
			packets_to_be_checked.append(packet)
			
	#sort all filtered packets based on sender id and message_id
	packets_to_be_checked.sort(key=lambda packet: (packet.sender_id, packet.message_id))
	
	for index, packet in enumerate(packets_to_be_checked[:-1]):
		#if current and next packet were sent by the same server
		if packets_to_be_checked[index+1].sender_id == packet.sender_id:
			#if the difference between messages ids is bigger than 2 => thee is a missing message
			if packets_to_be_checked[index+1].message_id - packet.message_id > 2:
				print("[Server update] The message %d from senderid:%d is missing", packet.message_id+2, packet.sender_id)
				#send a request to that server. The content is the ID of the missing message
				unicastMessage(KnownMessageID.RequestMissingMessage, MessageType.REQUESTMISSINGMESSAGE, packet.message_id+2, getCurrentServerDateTime(), (localhost, packet.sender_id))
			
	#check again after 30 seconds
	sleep(30)

t1 = Thread(target= thread_mainprocess, args=())
t1.start()

t2 = Thread(target= thread_sending_message, args=())
t2.start()

t3 = Thread(target = thread_decidetheleader, args = ())
t3.start()
t3.join()

t4 = Thread(target= thread_sendheartbeat, args=())
t4.start()

t5 = Thread(target= thread_checkservers, args=())
t5.start()

t6 = Thread(target= thread_check_missing_packets, args=())
t6.start()
