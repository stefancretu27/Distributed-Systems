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
#used for threads
from threading import Thread, Lock
from time import sleep
#import classes
from UDPServerModel import UDPServerModel
from DataPacketModel import DataPacketModel
from ClientModel import ClientModel
from MessageUtil import MessageUtil
from Enum import MessageType,SenderType,ConstantValues,MessageContent
from MessageHistoryModel import MessageHistoryModel
from GlobalInfo import GlobalInfo

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
	#for server in list_of_servers:	#getAddress to send msg to
		#if server != this_server:
	this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, message_id, message_type, message_content, message_datetime), \
	this_server.getDiscoveryAddress())

#used to send message to one entity server/client
def unicastMessage(message_id, message_type, message_content, message_datetime, target_address):
	this_server.socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, message_id, message_type, message_content, message_datetime), target_address)

def getStrListOfConnectedServers():
	strserver = ""
	if list_of_servers:
		lst_size = len(list_of_servers)
		idx = 0
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
	print ("------------ deactivate the old leader------------------------")
	for i, server in enumerate(list_of_servers):
		if server.port == global_info.getCurrentLeader():
			list_of_servers[i].deactivateTheRoleAsTheLeader()
			break

def removeTheLeader():
	print ("------------ removing the old leader------------------------")
	try:
		for i, server in enumerate(list_of_servers):
			if server.port == global_info.getCurrentLeader():
				del list_of_servers[i]
				break
	except:
		e = sys.exc_info()[0]
		print("Exception removing the server", e)

def removeTheServer(serverport):
	print ("------------ removing the server------------------------")
	try:
		for i, server in enumerate(list_of_servers):
			if server.port == serverport:
				del list_of_servers[i]
				break
	except:
		e = sys.exc_info()[0]
		print("Exception removing the server", e)

def resetLastSendingMessageDateTimeAllServers():
	for server_item in list_of_servers:
		server_item.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(getCurrentServerDateTime()))

def updateSenderLastSendingMessageDateTime(_port, _lastsendingmessagedatetime):
	if (len(list_of_servers) > 1):
		sender_server = getServerByPort(_port)
		if (sender_server is not None):
			sender_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(_lastsendingmessagedatetime))

isabletopingtheleader = True
checktheleader = True
alreadysentmessage = False

#store the info about the servers. It includes all servers (also self)
list_of_servers = list()

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
#
global_lock = Lock()

#inform the admin that this server is up
print('[Server update] Server is starting up on %s port %s' % (this_server.ip, this_server.port))	

#global list of sockets used by multiple threads
socket_list = [this_server.socket, this_server.discovery_socket]

#set thread and timer
def thread_decidetheleader():
	global alreadysentmessage, isabletopingtheleader, checktheleader, sent_message_id, this_server, list_of_servers, global_info, global_lock
	#starting thread
	sleep(10)

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
				print("============================ Thread decide the leader is started ================================")
				launchElection(this_server.port,MessageContent.SERVERALIVE)
				print("========================== Thread decide leader ended ====================================")

		if (global_info.getServerStatus() in [MessageType.LISTOFSERVERUPDATED]):
			print("global_info.getServerStatus()", global_info.getServerStatus())
			#get the leader from server list
			theleader = getTheLeaderFromServerList()
			sorted_list_of_server_by_port = sorted(list_of_servers, key=lambda x: x.port, reverse=True)

			print("theleader ",theleader.port)
			if ((theleader is None and this_server.port == sorted_list_of_server_by_port[0].port) or (theleader is not None and this_server.port > theleader.port)):
				#if the leader exist, deactivate its role
				if (theleader is not None):
					theleader.deactivateTheRoleAsTheLeader()

				theleader = this_server
				print("I am the leader now, and I will announce the message to everyone")
				#tell everyone that I am the leader
				voting_packet = DataPacketModel(getCurrentServerDateTime())
				sent_message_id += 2
				temp_msg_content = str(sorted_list_of_server_by_port[0].port)+"#"+MessageContent.SERVERALIVE
				# print("sending the message")
				voting_packet.buildPacket("voting", SenderType.SERVER, sent_message_id, MessageType.DECLARETHELEADER, temp_msg_content, voting_packet.receivedDateTime, this_server.port)
				this_server.sending_messages_queue.append(voting_packet)
				# print("after sending the message")
			else:
				print("I don't have a chance to be the leader. So, I will update my leader with the existing one : %s"%(str(theleader.port)))

			#update my status to running and set I'm the leader
			theleader.activateTheRoleAsTheLeader()
			global_info.setServerStatus(MessageType.RUNNING)
			global_info.setCurrentLeader(theleader.port)
	except:
		e = sys.exc_info()[0]
		print("Do not worry, it is going to be fine", e)
	finally:
		print("the leader:", global_info.getCurrentLeader(), ", server status:", global_info.getServerStatus(), ", am i the leader?",this_server.isTheLeader())

def thread_mainprocess():
	global alreadysentmessage, sent_message_id, this_server, list_of_servers, global_info 
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
					multicastMessageToServers(0, MessageType.SERVERUP, MessageUtil.convertDateTimeToString(this_server.getJoiningDateTime()), message_datetime)

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
					#add packet in message queues
					if temp_packet not in this_server.received_messages_queue:
						#append packet in the server's message log
						this_server.received_messages_queue.append(temp_packet)
						#append packet in the server's packets buffer used for processing messages
						this_server.message_buffer.append(temp_packet)
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
					sending_packet.buildPacket(temp_server.getAddress(), SenderType.SERVER, packet.message_id + 1, MessageType.RECEIVEDMESSAGE, packet.message_content, packet.sendingDateTime, this_server.port)
					this_server.sending_messages_queue.append(sending_packet)
				
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
				
				###for the time being, this verification is redundant, since all servers sent SERVERUP continuously but not other message type. 
				if ((global_info.getServerStatus() in [MessageType.SERVERUP, MessageType.RUNNING, MessageType.REQUESTLISTOFSERVER, MessageType.ACKNOWLEDGEMENTFROMALIVESERVER, \
				MessageType.LISTOFSERVERUPDATED]) and packet.message_type  == MessageType.SERVERUP):
					# print("global_info.getServerStatus()", global_info.getServerStatus(), "message type", message_type)
					#create a temporary server model with the received attributes
					temp_server = UDPServerModel(localhost, packet.sender_id)
					serverdatetime_received_acknowledgement = getCurrentServerDateTime()
					temp_server.setLastSendingMessageDateTime(MessageUtil.convertStringToDateTime(packet.receivedDateTime))

					# print("list of server", len(getLitsOfServerPorts()), "port baru", temp_server.port)
					if temp_server.port not in getLitsOfServerPorts():
						temp_server.setJoiningDateTime(MessageUtil.convertStringToDateTime(packet.message_content))
						list_of_servers.append(temp_server)
						print ('[Server update] A new server is up. It runs on the address:%s. My global status is %s'%(str(temp_server.getAddress()), global_info.getServerStatus()))
						print ('[Server update] The current running servers are:')
						showConnectedServers()
						if (global_info.getServerStatus() == MessageType.RUNNING):
							#send acknowledgement to the newly added server
							print("I send acknowledgement message to the newly added server")
							unicastMessage(-4, MessageType.ACKNOWLEDGEMENTFROMALIVESERVER, 'ack from alive server', packet.receivedDateTime, temp_server.getAddress())
							
				#if a new server wants to connect during the election, then send the message to try again in a few moments
				if (packet.message_type == MessageType.SERVERUP and (global_info.getServerStatus() in [MessageType.VOTING])):
					#if the sender is not on my server list, then refuse to connect
					if (packet.sender_id not in getLitsOfServerPorts()):
						unicastMessage(-5, MessageType.SERVERBUSY, 'server busy', packet.receivedDateTime, temp_server.getAddress())
					
				#if the server status is up and the message type is declare the leader
				#MessageType.SERVERUP
				if ((global_info.getServerStatus() in [MessageType.RUNNING, MessageType.SERVERUP, MessageType.VOTING]) and packet.message_type == MessageType.DECLARETHELEADER):
					print("global_info.getServerStatus()", global_info.getServerStatus(), "message type", packet.message_type, " content", packet.message_content)
					arrmessagecontent = packet.message_content.split("#")
					theleaderport = int(arrmessagecontent[0])
					leaderstatus = arrmessagecontent[1]

					print("total active server",len(list_of_servers))

					if ((global_info.getServerStatus() == MessageType.SERVERUP and len(list_of_servers)> 1)
						or global_info.getServerStatus() in [MessageType.RUNNING, MessageType.VOTING]):

						#deactivate the leader and or remove the leader
						if (leaderstatus == MessageContent.SERVERALIVE):
							deactivateTheLeader()
						else:
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
								print("I can't find the leader on my list of servers")

						updateSenderLastSendingMessageDateTime(packet.sender_id, packet.receivedDateTime)
						#set the params of global info
						global_info.setCurrentLeader(theleaderport)
						global_info.setServerStatus(MessageType.RUNNING)
						print("Voting done. My current global info is: server status:%s and the leader is %s"%(global_info.serverstatus,str(global_info.getCurrentLeader())))

					
				if (global_info.getServerStatus() == MessageType.RUNNING and packet.message_type == MessageType.REQUESTLISTOFSERVER):
					print("I got message from %s with message type %s"%(str(packet.sender_id), packet.message_type))
					#announce the list of servers
					print("I will send the list of existing servers to %s"%(str(packet.sender_id)))
					unicastMessage(-6, MessageType.LISTOFEXISTINGSERVERS, getStrListOfConnectedServers(), getCurrentServerDateTime(), getExisitngServerByPort(packet.sender_id).getAddress())

				#if slave goes down and my status is running
				if ((global_info.getServerStatus() in [MessageType.RUNNING, MessageType.VOTING]) and packet.message_type == MessageType.SLAVEDOWN):
					print("I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))
					removeTheServer(int(packet.message_content))
					print("I have updated my server list.")
					showConnectedServers()

				#if voting is launched and my status is running
				if ((global_info.getServerStatus() in [MessageType.RUNNING, MessageType.SERVERUP,MessageType.VOTING]) and packet.message_type == MessageType.VOTING):
					#if the sender is on my server list, then allow them to participate in election
					if (packet.sender_id in getLitsOfServerPorts()):
						print("I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))
						arrmessagecontent = packet.message_content.split("#")
						theleaderport = int(arrmessagecontent[0])
						theleaderstatus = arrmessagecontent[1]

						#if the leader has been changed
						if (theleaderport == global_info.getCurrentLeader() or global_info.getServerStatus() == MessageType.SERVERUP):
							#set my status to voting
							global_info.setServerStatus(MessageType.VOTING)

							#remove the previous leader
							if (theleaderstatus ==MessageContent.SERVERCRASH):
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
								this_server.sending_messages_queue.append(voting_packet)
								#change my status to running
								global_info.setServerStatus(MessageType.RUNNING)
								print("I'm the leader now since I have the highest port over the others. I will multicast this message")
						else:
							#get server by port
							previousleader = getExisitngServerByPort(theleaderport)
							if (previousleader is None):
								#send the current leader to the sender
								print("the leader has changed, the newest one is %s"%(str(global_info.getCurrentLeader())))
								unicastMessage(-7, MessageType.ANNOUNCELEADER, str(global_info.getCurrentLeader()), packet.receivedDateTime, (localhost, packet.sender_id))

						#update the last sending message datetime of the sender
						updateSenderLastSendingMessageDateTime(packet.sender_id, packet.receivedDateTime)

								#if there is an announcement of the new leader and my status is running
				if (global_info.getServerStatus() == MessageType.RUNNING and packet.message_type == MessageType.ANNOUNCELEADER):
					print("I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))
					#get server by port
					theleader = int(packet.message_content)
					theleader = getExisitngServerByPort(theleader)

					if (theleader is not None):
						if (theleader.port != global_info.getCurrentLeader()):
							#remove the previous leader
							removeTheLeader()

							#activate the role of the server as the leader
							theleader.activateTheRoleAsTheLeader()
							#set the params of global info
							global_info.setServerStatus(MessageType.RUNNING)
							global_info.setCurrentLeader(theleader.port)

					#update the last sending message datetime of the sender
					updateSenderLastSendingMessageDateTime(packet.sender_id, packet.receivedDateTime)
					print("This is my current global info:%s, current leader:%s"%(global_info.getServerStatus(), str(global_info.getCurrentLeader())))

				#if server sent its heart beat
				if ((global_info.getServerStatus() in [MessageType.RUNNING, MessageType.VOTING]) and packet.message_type == MessageType.HEARTBEAT):
					print("I got message from %s with message type %s and the content is %s"%(str(packet.sender_id),packet.message_type, packet.message_content))
					#update the last sending message datetime of the sender
					updateSenderLastSendingMessageDateTime(packet.sender_id, packet.receivedDateTime)
					
				if ((global_info.getServerStatus() in [MessageType.SERVERUP, MessageType.SERVERBUSY]) and packet.message_type == MessageType.ACKNOWLEDGEMENTFROMALIVESERVER):
					print("I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))
					#update server status
					global_info.setServerStatus(MessageType.ACKNOWLEDGEMENTFROMALIVESERVER)
					#request list of server
					print("I request list of the servers to the group. My global status is %s"%(global_info.getServerStatus()))
					multicastMessageToServers(-3, MessageType.REQUESTLISTOFSERVER, "req list of servers", getCurrentServerDateTime())

				if (global_info.getServerStatus() == MessageType.SERVERUP and packet.message_type == MessageType.SERVERBUSY):
					#set already sent message to true
					alreadysentmessage = True
					print("=================== Attention! Server is busy now, please try again in a few minutes====================")
					#update server status
					global_info.setServerStatus(MessageType.SERVERBUSY)
					#quit
					this_server.closeSocket()
					sys.exit(0)	
				
				if ((global_info.getServerStatus() in [MessageType.ACKNOWLEDGEMENTFROMALIVESERVER]) and packet.message_type == MessageType.LISTOFEXISTINGSERVERS):
					print("I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))
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
					print("List of servers has been updated")
					#update my global info if my status is not running or voting
					global_info.setServerStatus(MessageType.LISTOFSERVERUPDATED)

				if (packet.message_type == MessageType.ACKNOWLEDGEMENTVOTING):
					print("I got message from %s with message type %s and the content is %s"%(str(packet.sender_id), packet.message_type, packet.message_content))
					global_info.setServerStatus(MessageType.ACKNOWLEDGEMENTVOTING)
					#update the last sending message datetime of the sender
					updateSenderLastSendingMessageDateTime(packet.sender_id, packet.receivedDateTime)

				#Server handles client related events
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
					#server_packet.list_of_receivers = list()
					sent_message_id += 2
					server_packet.buildPacket("recv from client", SenderType.SERVER, sent_message_id, MessageType.JOINROOM, packet.sender_address, packet.receivedDateTime, this_server.port)
					#send message to the other server instances to inform them that a new client has connected as they need to update their client group view
					this_server.sending_messages_queue.append(server_packet)
					
					#build a packet
					client_packet = DataPacketModel(getCurrentServerDateTime())
					client_packet.buildPacket(temp_client, SenderType.CLIENT, -1, MessageType.JOINROOM, packet.sender_address, packet.receivedDateTime, this_server.port)
					#send message to the other connected clients
					this_server.sending_messages_queue.append(client_packet)
					
				#If the client quit the chat, the client application sends a 'quit' message.
				if (packet.message_type == MessageType.LEFTROOM):
					#make sure the client attributes are in this_server's client group view
					if this_server.isClientInList(temp_client):
						#record leving datetime
						temp_client.setLeavingDateTime(temp_packet.receivedDateTime)
						
						#build a packet
						server_packet = DataPacketModel(getCurrentServerDateTime())
						#server_packet.list_of_receivers = list()
						sent_message_id += 2
						server_packet.buildPacket("recv from client", SenderType.SERVER, sent_message_id, MessageType.LEFTROOM, packet.sender_address, packet.receivedDateTime, this_server.port)
						#send message to the other server instances to inform them that a new client has left as they need to update their client group view
						this_server.sending_messages_queue.append(server_packet)
						
						#build a packet
						client_packet = DataPacketModel(getCurrentServerDateTime())
						client_packet.buildPacket(temp_client, SenderType.CLIENT, -1, MessageType.LEFTROOM, packet.sender_address, packet.receivedDateTime, this_server.port)
						#send message to the other connected clients
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
								
						#build a packet
						client_packet = DataPacketModel(getCurrentServerDateTime())
						#this_server.multicastMessagetoClients(temp_client, MessageType.NORMALCHAT, packet.receivedDateTime)
						client_packet.buildPacket(temp_client, SenderType.CLIENT, -1, MessageType.NORMALCHAT, packet.sender_address, packet.receivedDateTime, this_server.port)
						#send message to the other connected clients
						this_server.sending_messages_queue.append(client_packet)

			#remove processed packet from the received_messages_queue
			this_server.message_buffer.remove(packet)

################################### additional thread ##############################################3
def thread_sendpacket():
	while True:
		#this_server.sending_messages_queue.sort(key=lambda packet: packet.sendingDateTime)
		for packet in this_server.sending_messages_queue:
			if (packet.sender_type == SenderType.SERVER):
				# print (packet.message_id, packet.message_type, packet.sender_id, packet.message_content)
				if packet.metadata == "recv from client" or packet.metadata == "voting":
					multicastMessageToServers(packet.message_id, packet.message_type, packet.message_content, packet.sendingDateTime)

					#if all servers in the group view received the message, removed the message from the list. Valid only for IP server multicast
					packet.list_of_receivers.sort(key=lambda server: server.port)

					if list_of_servers == packet.list_of_receivers:
						this_server.sending_messages_queue.remove(packet)
					# print ("Servers", [server.port for server in list_of_servers])
					# print ("Receivers", [server.port for server in packet.list_of_receivers])

				else:
					unicastMessage(packet.message_id, packet.message_type, packet.message_content, packet.sendingDateTime, packet.metadata)
					this_server.sending_messages_queue.remove(packet)

			if (packet.sender_type == SenderType.CLIENT):
				this_server.multicastMessagetoClients(packet.metadata, packet.message_type, packet.sendingDateTime)
				this_server.sending_messages_queue.remove(packet)

########################################################################
isAbleToSendHeartBeat = True
def thread_sendheartbeat():
	global isAbleToSendHeartBeat
	while True:
		if (isAbleToSendHeartBeat):
			# print("====================== I send my heart beat=========================")
			multicastMessageToServers(-2,  MessageType.HEARTBEAT, "heartbeat", getCurrentServerDateTime())
			isAbleToSendHeartBeat = False
			#set sleeping time to 3
			sleep(3)
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
					print("Exception in thread check the leader", e)
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
							print("Exception in thread_checkservers", e)

#ping each server
def thread_checkeachserver(port,istheleader):
	global sent_message_id, this_server, list_of_servers
	try:
		#get exisiting server
		existing_server = getExisitngServerByPort(port)
		#get the first delta of existing server
		first_datetimesendingmessage = existing_server.getLastSendingMessageDateTime()
		first_delta = (MessageUtil.convertStringToDateTime(getCurrentServerDateTime()) - first_datetimesendingmessage).total_seconds()
		# print("checking server status %s, first delta:%s"%(str(port),str(first_delta)))
		#compare delta value with its maximum
		if (first_delta > ConstantValues.DELTAMAX):
			#wait for 15 seconds
			sleep(15)
			#get the second delta of existing server
			second_datetimesendingmessage = getExisitngServerByPort(port).getLastSendingMessageDateTime()
			second_delta = (MessageUtil.convertStringToDateTime(getCurrentServerDateTime()) - second_datetimesendingmessage).total_seconds()
			print("checking server status %s, second delta:%s"%(str(port),str(second_delta)))

			#again, compare delta value with its maximum threshold
			if (second_delta > ConstantValues.DELTAMAX and getExisitngServerByPort(port) is not None):
				#get the existing server
				existingserver = getExisitngServerByPort(port)
				if (existingserver is not None):
					if (istheleader):
						print("I am checking the leader")
						#launch leader election
						launchElection(existingserver.port, MessageContent.SERVERCRASH)
					else:
						#inform servers in multicast group that someone crash
						print("I am checking the slaves")
						#remove the corresponding server
						removeTheServer(existing_server.port)

						#send multicast message to all other servers
						voting_packet = DataPacketModel(getCurrentServerDateTime())
						sent_message_id += 2
						temp_msg_content = str(existingserver.port)
						voting_packet.buildPacket("voting", SenderType.SERVER, sent_message_id, MessageType.SLAVEDOWN, temp_msg_content, voting_packet.receivedDateTime, this_server.port)
						this_server.sending_messages_queue.append(voting_packet)
						#this_server.discovery_socket.sendto(MessageUtil.constructMessage(this_server.port, SenderType.SERVER, MessageType.SLAVEDOWN, str(existingserver.port), \
						#getCurrentServerDateTime()), this_server.getDiscoveryAddress())
						print("server %s is going down. The multicast message has been sent to the other servers"%(str(port)))
						showConnectedServers()

						#then re-launch the election
						#print("----------------------Relaunch the election because someones dies----------------------")
						#launchElection(global_info.getCurrentLeader(), MessageContent.SERVERALIVE)
	except:
		e = sys.exc_info()[0]
		print("Exception in thread_checkservers. Do not worry, it's going to be fine :)", e)

#method to launch an election
def launchElection(port,leaderstatus):
	global sent_message_id 
	try:
		if (leaderstatus == MessageContent.SERVERCRASH):
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
			this_server.sending_messages_queue.append(voting_packet)
			#set global status to running
			global_info.setServerStatus(MessageType.RUNNING)
			print("I am the leader now and this is my global info:%s , %s"%(global_info.getServerStatus(), str(global_info.getCurrentLeader())))

		#otherwise, launch election
		else:
			print("Launching election")
			#announce that I'm the leader by sending message to multicast group
			voting_packet = DataPacketModel(getCurrentServerDateTime())
			sent_message_id += 2
			temp_msg_content = str(port)+"#"+leaderstatus
			voting_packet.buildPacket("voting", SenderType.SERVER, sent_message_id, MessageType.VOTING, temp_msg_content, voting_packet.receivedDateTime, this_server.port)
			this_server.sending_messages_queue.append(voting_packet)

			#set server status and global status
			global_info.setServerStatus(MessageType.VOTING)
			#wait for 15 seconds
			sleep(15)
			print("My status after 15 seconds", global_info.getServerStatus(), " the leader:",global_info.getCurrentLeader())
			#if the status is still voting after 15 seconds, then
			if (global_info.getServerStatus() == MessageType.VOTING and (port == global_info.getCurrentLeader())):
				#sort the members by port
				sorted_list_of_server_by_port = sorted(list_of_servers, key=lambda x: x.port, reverse=True)

				#get the delta of each server
				for server in sorted_list_of_server_by_port:
					if server.port != this_server.port:
						server_datetimesendingmessage = server.getLastSendingMessageDateTime()
						server_delta = (MessageUtil.convertStringToDateTime(getCurrentServerDateTime()) - server_datetimesendingmessage).total_seconds()
						#if server delta greater than maximum treshold
						if (server_delta > ConstantValues.DELTAMAX):
							#remove the corresponding server
							removeTheServer(server.port)
							#send multicast message to all other servers
							voting_packet = DataPacketModel(getCurrentServerDateTime())
							sent_message_id += 2
							temp_msg_content = str(server.port)
							voting_packet.buildPacket("voting", SenderType.SERVER, sent_message_id, MessageType.SLAVEDOWN, temp_msg_content, voting_packet.receivedDateTime, this_server.port)
							this_server.sending_messages_queue.append(voting_packet)
							print("server %s is going down. The multicast message has been sent to the other servers"%(str(server.port)))

							#then re-launch the election
							print("----------------------Relaunch the election because someones dies----------------------")
							launchElection(global_info.getCurrentLeader(), MessageContent.SERVERCRASH)

							break
			showConnectedServers()
	except:
		print("Do not worry, it is going to be fine")


t1 = Thread(target= thread_mainprocess, args=())
t1.start()

t2 = Thread(target = thread_sendpacket, args=())
t2.start()

t3 = Thread(target = thread_decidetheleader, args = ())
t3.start()
t3.join()

t3 = Thread(target= thread_sendheartbeat, args=())
t3.start()

t4 = Thread(target= thread_checkservers, args=())
t4.start()
