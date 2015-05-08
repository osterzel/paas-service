__author__ = 'oliver'

from os.path import dirname, realpath
import sys

sys.path.append(dirname(realpath(__file__)) + '../../' )

from common.datastore import Datastore

class GlobalConfig(object):

    def __init__(self):
        self.datastore = Datastore()

    def get_hosts(self):
        hosts = self.datastore.getContainerHosts()
        return hosts

    def add_hosts(self, data):
        '''
            This accepts a json request of { "hosts" : [ array of hosts to add ] }
        '''

        for host in data['hosts']:
            self.datastore.addContainerHost(host)

        return self.get_hosts()

    def remove_hosts(self, data):
        '''
            This accepts a json request of { "hosts" : [ array of hosts to remove ] }
        '''

        for host in data['hosts']:
            self.datastore.deleteContainerHost(host)

        return self.get_hosts()
