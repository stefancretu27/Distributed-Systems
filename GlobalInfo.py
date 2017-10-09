class GlobalInfo:
    serverstatus = None
    currentleader = None

    #Methods
    def setServerStatus(self, new_serverstatus):
        self.serverstatus = new_serverstatus

    def setCurrentLeader(self, new_leader):
        self.currentleader = new_leader

    def getCurrentLeader(self):
        return (self.currentleader)

    def getServerStatus(self):
        return (self.serverstatus)
