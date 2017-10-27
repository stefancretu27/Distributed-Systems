def enum(**named_values):
    return type('Enum', (), named_values)


MessageType = enum(JOINROOM='joinroom', ANNOUNCELEADER='announceleader', ACKNOWLEDGEFROMSERVER='acknowledgefromserver', NORMALCHAT='normalchat', ANNOUNCEMENT='announcement', \
LEFTROOM='leftroom', SERVERUP='serverup', SERVERDOWN='serverdown', VOTING='voting', RUNNING='running', DECLARETHELEADER='declareleader', NEWSERVER='newserver', \
LISTOFEXISTINGSERVERS='listexistingservers', PINGTHELEADER='pingtheleader',ACKNOWLEDGEMENTPINGTHELEADER='acknowledgementpingtheleader',PAUSERUNNING='pauserunning', \
ACKNOWLEDGEMENTVOTING='acknowledgementvoting', WAITINGFORACKNOWLEDGMENT='waitingforacknowledgement',ANNOUNCELEADERAFTERJOIN='announceleaderafterjoin',SLAVEDOWN='slavedown', \
PINGTHESLAVE='pingtheslave',ACKNOWLEDGEMENTPINGTHESLAVE='acknowldegementpingtheslave', SERVERUPINPROGRESSEXCHANGINGINFORMATION='serverupinprogressexchanginginformation', \
<<<<<<< HEAD
ACKNOWLEDGEMENTFROMALIVESERVER='acknowledgementfromaliveserver', REQUESTLISTOFSERVER = 'requestlistofserver',SERVERBUSY='serverbusy', LISTOFEXISTINGCLIENTS='lisofexistingclients',\
DECIDINGTHELEADER='decidingtheleader', HEARTBEAT='heartbeat', RECEIVEDMESSAGE='receivedmessage',  LISTOFCLIENTSUPDATED='listofclientsupdated', REQUESTLISTOFCLIENTS='requestlistofclients',
CLIENTREJOIN = 'clientrejoin',ANNOUNCEMENTSLAVEDOWN='announcementslavedown')
=======
ACKNOWLEDGEMENTFROMALIVESERVER='acknowledgementfromaliveserver',LISTOFCLIENTSUPDATED='listofclientsupdated', REQUESTLISTOFSERVER = 'requestlistofserver',SERVERBUSY='serverbusy', \
DECIDINGTHELEADER='decidingtheleader', HEARTBEAT='heartbeat', RECEIVEDMESSAGE='receivedmessage', REQUESTLISTOFCLIENTS='requestlistofclients',LISTOFEXISTINGCLIENTS='lisofexistingclients')
>>>>>>> 07f1e73416a08c56f144dd5f5afff75b6df8a810
SenderType = enum(CLIENT='client', SERVER='server')
MessageContent = enum(QUIT='~q',SERVERALIVE='0',SERVERCRASH='1',NONE='none')
ConstantValues = enum(DELTAMAX=30)
