import socket
#used for packing IPv4 address
import struct

from ClientModel import ClientModel
from MessageUtil import MessageUtil
from Enum import MessageType,SenderType

#use UDP socket: it is connectionless and does not guarantee the data delivery. A packet is built with destination information and then is sent
class UDPServerModel:
#a server is identified based on its ip and port
	ip = None
	port = None
#socket object used for communication with clients and to update the other servers with newest client info (general socket)
	socket = None

#socket object used for discovery and fault tolerance
	discovery_socket = None
#dynamic discovery global data
	discovery_multicast_group = '224.1.1.1'
	discovery_multicast_port = 12000

#message
	message = None

#store the info about the other servers. It includes all servers.
	list_of_servers = list()
#store all connected clients in a global list	
	list_of_clients = list()

#Methods
#constructor
	def __init__(self, new_ip, new_port):
		self.port = new_port
		self.ip = new_ip

#override operators
	#a server is the same if it has the same IP address
	def __eq__(self, new_UDPserver):
		return self.port == new_UDPserver.port
	#override not equal operator
	def __ne__(self, new_UDPserver):
		return self.port != new_UDPserver.port

#setters
	def setIP(self, new_ip):
		self.ip = new_ip
	def setPort(self, new_port):
		self.port = new_port

#getters
	#build ID
	def getID(self):
		return "%s:%s"%(self.ip, self.port)
	#build address as pair of ip and port
	def getAddress(self):
		return (self.ip, self.port)

	def getDiscoveryAddress(self):
		return (self.discovery_multicast_group, self.discovery_multicast_port)

	#method for setting the communication on the general socket
	def openSocket(self):
		#create UDP socket
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#accept connections on the port given as argument to the process and on the IP provided at object creation
		self.socket.bind((self.ip, self.port))

	def initializeDiscoverySocket(self):
		# Create the socket
		self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#reuse the multicast address sso multiple server instances can bind it and use it
		self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# Bind to the discovery address
		self.discovery_socket.bind(self.getDiscoveryAddress())
		#Convert an IPv4 address from dotted-quad string format to 32-bit packed binary format
		group = socket.inet_aton(self.discovery_multicast_group)
		#The option value is 8-byte representation of multicast group address and of the interface on which the server should listen for traffic. IP can be specified
		mreq = struct.pack('4sL', group, socket.INADDR_ANY)
		# Tell the operating system to add the socket to the multicast group on all interfaces.
		self.discovery_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


#list of clients related operations
	#for various reasons a client will disconnect => update the list of clients
	def disconnectClient(self, this_client):
		if self.list_of_clients:
			return [client for client in self.list_of_clients if client != this_client]
		else:
			return []
	#display the port and ip of all clients
	def showConnectedClients(self):
		if self.list_of_clients:
			for client in self.list_of_clients:
				print "   ",(client.address)
		else:
			print ('[Client update] No clients are currently connected in the system')
	#search if a client is connected	
	def isClientInList(self, this_client):
		for client in self.list_of_clients:
			if client == this_client:			
				return True
		return False

	#send a message to all connected clients but to the one that sent it
	def multicastMessagetoClients(self, this_client, message_type, serverdatetime):
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
			multicast_senderid = "%s:%s"%(self.ip, self.port)

		#multicast the message
		for client in self.list_of_clients:
			if (client == this_client):
				if (message_type == MessageType.JOINROOM):
					self.socket.sendto(MessageUtil.constructMessage(multicast_senderid, multicast_sendertype, MessageType.ACKNOWLEDGEFROMSERVER, this_client.getJoiningDateTime(), multicast_datetime), client.address)
			else:
				self.socket.sendto(MessageUtil.constructMessage(multicast_senderid, multicast_sendertype, message_type, multicast_message, multicast_datetime), client.address)

#list of servers related operations
	#if the server goes down, remove it from the list of servers
	def disconnectServer(self, removed_server):
		if self.list_of_servers and self != removed_server:
			return [server for server in self.list_of_servers if server != removed_server]
		else:
			return []
	#display the port and ip of the other servers
	def showConnectedServers(self):
		if self.list_of_servers:
			for server in self.list_of_servers:
				print "   ",(server.ip, server.port)
		else:
			print ('[Server update] No other servers are currently connected to this server:', self.ip)

	def getConnectedServersAddresses(self):
		if self.list_of_servers:		
			return [server.getAddress() for server in self.list_of_servers if server.default == 0]
		else:
			return []

	def getConnectedClientsAddresses(self):
		if self.list_of_clients:		
			return [client.getAddress() for client in self.list_of_clients]
		else:
			return []

	def multicastMessageToServers(self, message_type, message_content, message_datetime):
		for server in self.list_of_servers:	#getAddress to send msg to
			if server != self:
				self.socket.sendto(MessageUtil.constructMessage(self.getAddress(), SenderType.SERVER, message_type, message_content, message_datetime), server.getAddress())

	#used to send message to one entity server/client
	def unicastMessage(self, message_type, message_content, message_datetime, target_address):
		self.socket.sendto(MessageUtil.constructMessage(self.getAddress(), SenderType.SERVER, message_type, message_content, message_datetime), target_address)
