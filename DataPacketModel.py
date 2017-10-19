import json
import unicodedata
from MessageUtil import MessageUtil
from Enum import MessageType,SenderType

class DataPacketModel:
	message_id = None
	#used for receiving
	sender_address = None
	sender_packet = None
	receivedDateTime = None
	#used for both sending and receiving
	sender_id = None #port
	sender_type = None
	message_type = None
	message_content = None
	sendingDateTime = None
	#additionally data, used for sending
	metadata = None
	#used for reliability
	list_of_receivers = list()

	def __init__(self, new_receivedDateTime):
		self.receivedDateTime = new_receivedDateTime 
		self.list_of_receivers = list()
		
	def extractData(self):
		self.sender_id, self.sender_type, self.message_id, self.message_type, self.message_content, self.sendingDateTime = MessageUtil.extractMessage(self.sender_packet)
		
	def __eq__(self, new_packet):
		return self.sender_id == new_packet.sender_id  and self.sender_type == new_packet.sender_type and self.message_type == new_packet.message_type and \
		self.message_content == new_packet.message_content and self.sendingDateTime == new_packet.sendingDateTime and self.message_id == new_packet.message_id

	def __ne__(self, new_packet):
		return not(self.__eq__)
		
	def buildPacket(self, metadata, sender_type, message_id, message_type, message_content, sendingDateTime, sender_id):
		self.sender_type = sender_type
		self.message_id = message_id 
		self.message_type = message_type 
		self.message_content = message_content 
		self.sendingDateTime = sendingDateTime
		self.metadata = metadata
		self.sender_id = sender_id
