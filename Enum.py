def enum(**named_values):
    return type('Enum', (), named_values)


MessageType = enum(JOINROOM='joinroom', ANNOUNCELEADER='announceleader', ACKNOWLEDGEFROMSERVER='acknowledgefromserver', NORMALCHAT='normalchat', ANNOUNCEMENT='announcement', \
LEFTROOM='leftroom', SERVERUP='serverup', SERVERDOWN='serverdown', VOTING='voting', RUNNING='running', DECLARETHELEADER='declareleader', NEWSERVER='newserver', \
LISTOFEXISTINGSERVERS='listexistingservers', PINGTHELEADER='pingtheleader',ACKNOWLEDGEMENTPINGTHELEADER='acknowledgementpingtheleader',PAUSERUNNING='pauserunning', \
ACKNOWLEDGEMENTVOTING='acknowledgementvoting', WAITINGFORACKNOWLEDGMENT='waitingforacknowledgement',ANNOUNCELEADERAFTERJOIN='announceleaderafterjoin',SLAVEDOWN='slavedown', \
PINGTHESLAVE='pingtheslave',ACKNOWLEDGEMENTPINGTHESLAVE='acknowldegementpingtheslave', SERVERUPINPROGRESSEXCHANGINGINFORMATION='serverupinprogressexchanginginformation', \
ACKNOWLEDGEMENTFROMALIVESERVER='acknowledgementfromaliveserver', REQUESTLISTOFSERVER = 'requestlistofserver',SERVERBUSY='serverbusy', LISTOFEXISTINGCLIENTS='lisofexistingclients',\
DECIDINGTHELEADER='decidingtheleader', HEARTBEAT='heartbeat', RECEIVEDMESSAGE='receivedmessage',  LISTOFCLIENTSUPDATED='listofclientsupdated', REQUESTLISTOFCLIENTS='requestlistofclients',
CLIENTREJOIN = 'clientrejoin',CLIENTANNOUNCEMENTSERVERDOWN='clientannouncementserverdown')
SenderType = enum(CLIENT='client', SERVER='server')
MessageContent = enum(QUIT='~q',SERVERALIVE='0',SERVERCRASH='1',NONE='none')
ConstantValues = enum(DELTAMAX=30)
