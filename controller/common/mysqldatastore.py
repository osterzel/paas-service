import logging
import sys
from sqlalchemy import *
from config import Config
import config
import random
import time

class Datastore(object):
    def __init__(self, db=0):
        self.config = Config()
        self.engine = create_engine(self.config.sql_address, echo=True)

        #Now do some validation to confirm the schema we have in the database
        #The basic schema
        self.metadata = MetaData()

        self.application = Table('application', self.metadata,
                            Column('name', String(50), primary_key = True),
                            Column('type', String(100), nullable = True),
                            Column('docker_image', String(500), nullable = True),
                            Column('command', String(100), nullable = True),
                            Column('state', String(200), nullable = True),
                            Column('memory_in_mb', String(20), nullable = True),
                            Column('urls', String(1000), nullable = True),
                            Column('container_count', String(20), nullable = True)

        )

        self.environment = Table('environment', self.metadata,
                            Column('id', Integer, primary_key = True),
                            Column('key', String(1000), nullable = False),
                            Column('value', String(1000), nullable = False),
                            Column('application', ForeignKey("application.name"), nullable = False)
        )

        self.hosts = Table('hosts', self.metadata,
                Column('host', String(50), primary_key = True)
        )

        self.locks = Table('locks', self.metadata,
                Column('name', String(200), primary_key = True)
        )

        self.events = Table('events', self.metadata,
                Column('message', String(2000), nullable = True),
                Column('timestamp', Integer),
                Column('name', String(200), nullable = True)

        )

        self.metadata.create_all(self.engine)

        self.logger = logging.getLogger(__name__)

    def getConnection(self):
        return self.engine.connect()

    def getApplications(self):
        apps = list()
        for app in self.getConnection().execute(select([self.application])):
            apps.append(app['name'])
        return apps

    def getApplication(self, name):

        result = self.getConnection().execute(select([self.application]).where(self.application.c.name == name))
        try:
            return dict(result.fetchone())
        except:
            return dict()

    def getApplicationEnvironment(self, name):
        environment = dict()
        stmt = self.environment.select().where(self.environment.c.application == name)
        result = self.getConnection().execute(stmt)
        for row in result:
            environment[row.key] = row.value
        return environment


    def createApplication(self, name, data):
        ins = self.application.insert().values({k:v for k,v in data.items()})

        try:
            result = self.getConnection().execute(ins)
            return True
        except Exception as e:
            print "Exception: {}".format(e.message)
            return False

    def updateApplication(self, name, data):

        environment = None
        if "environment" in data:
            environment = data['environment']
            del data['environment']

        if not "state" in data:
            data['state'] = "OUT OF DATE, AWAITING DEPLOY"

        try:
            stmt = self.application.update().values({k:v for k,v in data.items()}).where(self.application.c.name == name)
            self.getConnection().execute(stmt)
        except Exception as e:
            print "THERE WAS A FAILURE: {}".format(e.message)

        if environment != None:
            self.updateApplicationEnvironment(name, environment)

    def updateApplicationEnvironment(self, name, data):

        #Get application_id
        for k,v in data.items():
            stmt = self.environment.select().where(self.environment.c.key == k).where(self.environment.c.application == name)
            data = self.getConnection().execute(stmt)

            stmt = None
            if v == None:
                stmt = self.environment.delete().where(self.environment.c.key == k).where(self.environment.c.application == name)
            else:
                if data.rowcount > 0:
                    stmt = self.environment.update().values(value = v).where(self.environment.c.key == k).where(self.environment.c.application == name)
                else:
                    stmt = self.environment.insert().values(key = k, value = v, application = name)

            self.getConnection().execute(stmt)

        return True

    def deleteApplication(self, name):
        try:
            self.deleteApplicationEnvironment(name)
            stmt = self.application.delete().where(self.application.c.name == name)
            self.getConnection().execute(stmt)
            return True
        except:
            raise Exception("Application not found")

    def deleteApplicationEnvironment(self, name):
        try:
            stmt = self.environment.delete().where(self.environment.c.application == name)
            self.getConnection().execute(stmt)
        except:
            pass

        return True

    def getContainerHosts(self):
        hosts = list()
        for host in self.getConnection().execute(select([self.hosts])):
            hosts.append(host[0])
        return hosts

    def addContainerHost(self, host):
        ins = self.hosts.insert().values(host = host)
        try:
            self.getConnection().execute(ins)
        except Exception as e:
            self.logger.info("Add Host error: {}".format(e))

    def deleteContainerHost(self, host):
        stmt = self.hosts.delete().where(self.hosts.c.host == host)
        try:
            self.getConnection().execute(stmt)
        except Exception as e:
            self.logger.info("Remove Host error: {}".format(e))


    def allocatePort(self):
        return random.randrange(30000, 60000)

    def releasePort(self, port):
        pass

    def createApplicationLock(self, name):
        try:
            stmt = self.locks.insert().values(name = name)
            self.getConnection().execute(stmt)
            return True
        except:
            return False

    def deleteApplicationLock(self, name):
        stmt = self.locks.delete().where(self.locks.c.name == name)
        self.getConnection().execute(stmt)

    def writeEvent(self, name, message):
        epoch_timestamp = time.time()
        stmt = self.events.insert().values( name = name, message = message, timestamp = epoch_timestamp)
        self.getConnection().execute(stmt)

    def getEvent(self, name):

        events_data = list()
        if ( name != "all"):
            stmt = self.events.select().where( self.events.c.name == name ).order_by(asc("timestamp")).limit(100)
        else:
            stmt = self.events.select().order_by(asc("timestamp")).limit(100)

        for event in self.getConnection().execute(stmt):
            events_data.append(event)

        return events_data





