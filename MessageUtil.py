import json
from datetime import datetime

class MessageUtil(object):

    @staticmethod
    def constructMessage(identifier_id, sender_type, message_type, message, datetime):
       json_format = {'id':identifier_id, 'sender_type':sender_type,'message_type':message_type, 'message':message, 'messagedatetime':datetime}
       #for python 2.7 please remove the encod() method
       return (json.dumps(json_format)).encode()

    @staticmethod
    def extractMessage(obj):
        json_object = json.loads(obj)
        return json_object['id'], json_object['sender_type'], json_object['message_type'], json_object['message'], json_object['messagedatetime']

    @staticmethod
    def convertStringToDateTime(str):
	    return datetime.strptime(str, "%Y-%m-%d %H:%M:%S")

    @staticmethod
    def convertDateTimeToString(obj):
	    return obj.strftime("%Y-%m-%d %H:%M:%S")
