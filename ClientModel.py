class ClientModel:
	message = None
	address = None

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
		self_address = new_address
