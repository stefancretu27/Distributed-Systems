def enum(**named_values):
    return type('Enum', (), named_values)


MessageType = enum(JOINROOM='joinroom', ANNOUNCELEADER='announceleader', ACKNOWLEDGEFROMSERVER='acknowledgefromserver', NORMALCHAT='normalchat', ANNOUNCEMENT='announcement', \
					LEFTROOM='leftroom', SERVERUP='serverup', SERVERDOWN='serverdown', VOTING='voting', RUNNING='running', DECLARETHELEADER='declareleader', NEWSERVER='newserver', \
					LISTOFEXISTINGSERVERS='listexistingservers', PINGTHELEADER='pingtheleader',ACKNOWLEDGEMENTPINGTHELEADER='acknowledgementpingtheleader',PAUSERUNNING='pauserunning', \
					ACKNOWLEDGEMENTVOTING='acknowledgementvoting', WAITINGFORACKNOWLEDGMENT='waitingforacknowledgement',ANNOUNCELEADERAFTERJOIN='announceleaderafterjoin',SLAVEDOWN='slavedown', \
					PINGTHESLAVE='pingtheslave',ACKNOWLEDGEMENTPINGTHESLAVE='acknowldegementpingtheslave', SERVERUPINPROGRESSEXCHANGINGINFORMATION='serverupinprogressexchanginginformation', \
					ACKNOWLEDGEMENTFROMALIVESERVER='acknowledgementfromaliveserver', REQUESTLISTOFSERVER = 'requestlistofserver',SERVERBUSY='serverbusy', \
					LISTOFEXISTINGCLIENTS='lisofexistingclients',DECIDINGTHELEADER='decidingtheleader', HEARTBEAT='heartbeat', RECEIVEDMESSAGE='receivedmessage',  \
					LISTOFCLIENTSUPDATED='listofclientsupdated', REQUESTLISTOFCLIENTS='requestlistofclients', CLIENTREJOIN = 'clientrejoin', \
					CLIENTANNOUNCEMENTSERVERDOWN='clientannouncementserverdown', REQUESTMISSINGMESSAGE = 'requestmissingmessage')
SenderType = enum(CLIENT='client', SERVER='server')
MessageContent = enum(QUIT='~q',SERVERALIVE='0',SERVERCRASH='1',NONE='none')
ConstantValues = enum(DELTAMAX=30)
KnownMessageID = enum(ServerUp = 0, ClientMsg = -1, HeartBeat = -2, RequestListofServers = -3, AckToNewServer = -4, ServerBusy = -5, SendListofServers = -6, AnnounceLeader = -7, \
						SendListOfClient = -8, RequestListofClients = -9, RequestMissingMessage = 10)
