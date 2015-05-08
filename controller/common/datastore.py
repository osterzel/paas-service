__author__ = 'oliver'
import logging
import sys
from config import Config
import config

class Datastore(object):
    def __init__(self, db=0):
        self.logger = logging.getLogger(__name__)

    def getConnection(self):
        self.logger.debug("Getting null connection to database")
        pass

    def getApplications(self):
        #Returns a list of application names
        pass

    def getApplication(self):
        #Returns a hash of the application details
        pass

    def getApplicationEnvironment(self):
        #Retruns a hash of environment variables
        pass

    def createApplicationEnvironment(self):
        pass

    def createApplication(self):
        pass

    def updateApplicationEnvironment(self):
        pass

    def updateApplication(self):
        pass

    def deleteApplication(self):
        pass

    def getContainerHosts(self):
        pass

    def addContainerHost(self):
        pass

    def deleteContainerHost(self):
        pass

    def allocatePort(self):
        pass

    def releasePort(self, port):
        pass

    def createApplicationLock(self, name):
        pass

    def deleteApplicationLock(self, name):
        pass

    def writeEvent(self, name, message):
        pass

    def getEvent(self, name):
        pass

config = Config()

if config.datastore == "redis":
    from redisdatastore import Datastore

if config.datastore == "mysql":
    from mysqldatastore import Datastore

