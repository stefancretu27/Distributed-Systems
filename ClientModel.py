class ClientModel:
	message = None
	address = None
	joiningdatetime = None
	leavingdatetime = None
	messagedatetime = None
	server_address = None

	def __init__ (self, input_message, input_address):
		self.message = input_message
		self.address = input_address

	#a client is the same if he has the same address(IP + port)
	def __eq__(self, new_client):
		return self.address == new_client.address

	#non equal operator
	def __ne__(self, new_client):
		return self.address != new_client.address

	#setters
	def setMessage(self, new_message):
		self.message = new_message

	def setAddress(self, new_address):
		self.address = new_address

	def setJoiningDateTime(self, new_joiningdatetime):
		self.joiningdatetime = new_joiningdatetime

	def setLeavingDateTime(self, new_leavingdatetime):
		self.joiningdatetime = new_leavingdatetime

	def setMessageDateTime(self, new_messagedatetime):
		self.messagedatetime = new_messagedatetime
	def setServerAddress(self, new_serveraddress):
		self.server_address = ('127.0.0.1', new_serveraddress)
	#getters
	def getAddress(self):
		return self.address

	def getJoiningDateTime(self):
		return self.joiningdatetime

	def getLeavingDateTime(self):
		return self.leavingdatetime

	def getMessageDateTime(self):
		return self.messagedatetime
