import socket
#used for packing IPv4 address
import struct

from ClientModel import ClientModel
from MessageUtil import MessageUtil
from Enum import MessageType,SenderType
from DataPacketModel import DataPacketModel

#use UDP socket: it is connectionless and does not guarantee the data delivery. A packet is built with destination information and then is sent
class UDPServerModel:
#a server is identified based on its ip and port
	ip = None
	port = None
#joining datetime
	joiningdatetime = None
	
#used for the other connected servers, to count how much time has passed since last message. Contatins the datetime when the message was sent by a server
	lastsendingmessagedatetime = None
	
#socket object used for communication with clients and to update the other servers with newest client info (general socket)
	socket = None
#socket object used for discovery and fault tolerance
	discovery_socket = None
	
#dynamic discovery global data
	discovery_multicast_group = '224.1.1.1'
	discovery_multicast_port = 12000
	
#leader status
	istheleader = False
#list of received messages to be processed and then removed
	message_buffer = list()
#list of received heartbeats processed and then removed
	recv_heartbeats_buffer = list()
#list of received messages. It acts like a message log, as the duplicate messages are rejected and the existing messages are not removed 
	received_messages_queue = list()
#list of messages to send
	sending_messages_queue = list()

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
	def setJoiningDateTime(self, new_joiningdatetime):
		self.joiningdatetime = new_joiningdatetime
	def setLastSendingMessageDateTime(self, new_lastsendingmessagedatetime):
		self.lastsendingmessagedatetime = new_lastsendingmessagedatetime
	def activateTheRoleAsTheLeader(self):
		self.istheleader = True
	def deactivateTheRoleAsTheLeader(self):
		self.istheleader = False

#getters
	#build ID
	def getID(self):
		return "%s:%s"%(self.ip, self.port)
	#build address as pair of ip and port
	def getAddress(self):
		return (self.ip, self.port)

	def getDiscoveryAddress(self):
		return (self.discovery_multicast_group, self.discovery_multicast_port)

	def getJoiningDateTime(self):
		return (self.joiningdatetime)

	def getLastSendingMessageDateTime(self):
		return (self.lastsendingmessagedatetime)

	def isTheLeader(self):
		return (self.istheleader)

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
		
	def closeSocket(self):
		self.socket.close()
