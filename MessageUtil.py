import json

class MessageUtil(object):

    @staticmethod
    def constructMessage(identifier_id, sender_type, message_type, message):
       json_format = {'id':identifier_id, 'sender_type':sender_type,'message_type':message_type, 'message':message}
       return json.dumps(json_format)

    @staticmethod
    def extractMessage(obj):
        json_object = json.loads(obj)
        return json_object['id'], json_object['sender_type'], json_object['message_type'], json_object['message']
