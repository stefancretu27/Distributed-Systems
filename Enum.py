def enum(**named_values):
    return type('Enum', (), named_values)

MessageType = enum(JOINROOM='joinroom', NORMALCHAT='normalchat', ANNOUNCEMENT='announcement',LEFTROOM='leftroom', SERVERUP='serverup', SERVERDOWN='serverdown')
SenderType = enum(CLIENT='client', SERVER='server')
MessageContent = enum(QUIT='~q')
