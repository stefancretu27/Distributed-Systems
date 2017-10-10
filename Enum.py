def enum(**named_values):
    return type('Enum', (), named_values)

MessageType = enum(JOINROOM='joinroom', ACKNOWLEDGEFROMSERVER='acknowledgefromserver', NORMALCHAT='normalchat', RECEIVEDVMESAGE='receivedmesage',LEFTROOM='leftroom', SERVERUP='serverup', \
SERVERDOWN='serverdown')
SenderType = enum(CLIENT='client', SERVER='server')
MessageContent = enum(QUIT='~q')
