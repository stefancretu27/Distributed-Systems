def enum(**named_values):
    return type('Enum', (), named_values)

MessageType = enum(JOINROOM='joinroom', ANNOUNCELEADER='announceleader', ACKNOWLEDGEFROMSERVER='acknowledgefromserver', NORMALCHAT='normalchat', ANNOUNCEMENT='announcement',LEFTROOM='leftroom', SERVERUP='serverup', SERVERDOWN='serverdown', VOTING='voting', RUNNING='running', DECLARETHELEADER='declareleader', NEWSERVER='newserver',LISTOFEXISTINGSERVERS='listexistingservers', PINGTHELEADER='pingtheleader',ACKNOWLEDGEMENTPINGTHELEADER='acknowledgementpingtheleader',PAUSERUNNING='pauserunning', ACKNOWLEDGEMENTVOTING='acknowledgementvoting', WAITINGFORACKNOWLEDGMENT='waitingforacknowledgement',ANNOUNCELEADERAFTERJOIN='announceleaderafterjoin',SLAVEDOWN='slavedown', PINGTHESLAVE='pingtheslave',ACKNOWLEDGEMENTPINGTHESLAVE='acknowldegementpingtheslave')
SenderType = enum(CLIENT='client', SERVER='server')
MessageContent = enum(QUIT='~q')
ConstantValues = enum(DELTAMAX=30)
