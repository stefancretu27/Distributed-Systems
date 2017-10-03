from ClientModel import ClientModel
class MessageHistoryModel:
	message = None
	ClientModel = None
	messagedatetime = None

	def __init__ (self, input_message, input_messagedatetime, input_clientmodel):
		self.message = input_message
		self.messagedatetime = input_messagedatetime
		self.ClientModel = input_clientmodel
