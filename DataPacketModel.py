import json
from MessageUtil import MessageUtil
from Enum import MessageType,SenderType

class DataPacketModel:
	sender_address = None
	sender_packet = None
	receivedDateTime = None
	
	sender_id = None #port 
	sender_type = None
	message_type = None
	message_content = None
	sendingDateTime = None
	
	
	def __init__(self, new_receivedDateTime):
		self.receivedDateTime = new_receivedDateTime
		
	def extractData(self):
		self.sender_id, self.sender_type, self.message_type, self.message_content, self.sendingDateTime = MessageUtil.extractMessage(self.sender_packet)

	
