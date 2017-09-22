import socket

#use UDP socket: it is connectionless and does not guarantee the data delivery. A packet is built with destination information and then is sent
class UDPServerModel:
	ip = None
	port = None
	leader = True
	socket = None

	def __init__(self, new_ip, new_port):
		self.port = new_port
		self.ip = new_ip

	#used for unicast. Reused for multicast woth additions from setMulticast method
	def openSocket(self):
		#create UDP socket
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#accept connections on the port given as argument to the process and on the IP provided at object creation
		self.socket.bind((self.ip, self.port))

	#a server is the same if it has the same IP address
	def __eq__(self, new_UDPserver):
		return self.ip == new_UDPserver.ip

	def setIP(self, new_ip):
		self.ip = new_ip

	def setPort(self, new_port):
		self.port = new_port
