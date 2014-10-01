__author__ = 'oliver'

class DockerClient(object):

    def __init__(self, cluster_name, hosts, auth, domain, options):
        self.name = cluster_name
        self.hosts = hosts
        self.auth = auth
        self.domain = domain
        self.options = options

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def create(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def delete(self):
        pass


