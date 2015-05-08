__author__ = 'oliver'

from os.path import dirname, realpath
import sys

sys.path.append(dirname(realpath(__file__)) + '../../' )

from datetime import datetime
import re
import docker
import requests

from common.paasevents import write_event, get_events
import common.exceptions as exceptions
from common.datastore import Datastore
import logging

class Applications(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.datastore = Datastore()

    def get_all(self):
        applications = self.datastore.getApplications()
        self.logger.debug("Getting application record")
        return { "data": applications }

    def get(self, name, containers=True):
        app_details = self.datastore.getApplication(name)

        if not app_details:
            self.logger.info("Unable to fetch application {}".format(name))
            raise Exception("Application not found")

        app_details['environment'] = self.datastore.getApplicationEnvironment(name)

        if "memory_in_mb" in app_details:
            app_details["memory_in_mb"] = str(app_details["memory_in_mb"])
        if not app_details:
            raise Exception

        #Fetch all containers that match this application
        if containers == True:
            containers = []
            for host in self.datastore.getContainerHosts():
                try:
                    c = docker.Client(base_url="http://{}:4243".format(host), version="1.12")
                    find_containers = c.containers()
                    for container in find_containers:
                            if name in str(container['Names']) and any(match in str(container['Names']) for match in [ '_web_', '_weburlcheck_' ]):
                                port = container['Names'][0].split('_')[-1]
                                containers.append("{}:{}".format(host, port))
                except:
                    self.logger.info("Unable to communicate with docker node while requesting application containers")

            app_details['containers'] = containers

        if not "urls" in app_details:
            try:
                main_url = app_details['name'] + app_details['global_environment']['domain_name']
            except:
                main_url = app_details['name']
            urls = main_url

            app_details['urls'] = main_url

        return app_details

    def create_application(self, data):

        name = data['name']

        application = self.datastore.getApplication(name)
        if not application:
            data = {
                        "name": name,
                        "type": "web",
                        "docker_image": "",
                        "state": "NEW",
                        "memory_in_mb": "128",
                        "command": "",
                        "urls": name,
                        "container_count": "2"
            }
            output = self.datastore.createApplication(name, data)
            self.logger.debug("Application created, datastore output: {}".format(output))
            write_event("CREATE APP", "Create app - {}".format(name), name)
        else:
            raise exceptions.ApplicationExists("Application already exists")

        return self.get(name)

    def update_application(self, name, data):
        #Make sure keys are valid
        self.logger.debug("Starting update of application")
        valid_keys = [ "memory_in_mb", "docker_image", "command", "urls", "type", "restart", "container_count", "environment", "name"]
        for key in data:
            print key
            if not any(x in key for x in valid_keys):
                raise Exception("Invalid key '{}' specified in data".format(key))

        if not self.datastore.getApplication(name):
            raise Exception("Application not found")
        if self.datastore.getApplication(name)['state'] == "deleting":
            raise Exception("Applicaton scheduled for deletion")

        self.logger.debug("Fetching application record")
        current_record = self.datastore.getApplication(name)
        current_environment = self.datastore.getApplicationEnvironment(name)
        self.logger.debug("Finished fetching application")

        if "restart" in data:
            del data['restart']
            try:
                new_counter = int(current_environment['RESTART']) + 1
            except KeyError:
                new_counter = 1

            if not "environment" in data:
                data['environment'] = {}
                data['environment']['RESTART'] = new_counter

            write_event("UPDATED APP", "App {}, restart called".format(name), name)

        if "environment" in data:
            #Check slug_url, if not valid return error
            if "SLUG_URL" in data["environment"].keys():
                try:
                    response = requests.get(data["environment"]["SLUG_URL"], timeout=2, stream=True)
                    if response.status_code != 200:
                        raise Exception
                except Exception as e:
                    write_event("UPDATE APP", "Failed updating app, slug url {} invalid or inaccessible".format(data['environment']['SLUG_URL']), name)
                    raise Exception("Slug URL {} is either invalid or inaccessible".format(data["environment"]["SLUG_URL"]))

            if "PORT" in data["environment"].keys():
                raise Exception

        self.logger.debug("Calling datastore update")
        result = self.datastore.updateApplication(name, data)
        self.logger.debug("Finished datastore update")

        #new_record = self.datastore.getApplication(name)
        #new_environment = self.datastore.getApplicationEnvironment(name)

        #env_diff = set(set(current_environment.items()) ^ set(new_environment.items()))
        #diff = set(set(current_record.items()) ^ set(new_record.items()))
        self.logger.debug("Finished update of application")

        write_event("UPDATED APP", "App {} was updated".format(name), name)

        return self.get(name)

    def delete_application(self, name):
        if not self.datastore.getApplication(name):
            raise Exception("Application not found")

        data = self.datastore.getApplication(name)
        port = None
        if "port" in data:
            port = data['port']

        self.datastore.deleteApplication(name)

        write_event("DELETE APP", "Deleted app - {}".format(name), name)
        return { "message": "Application {} deleted".format(name), "app_port": port}

    def set_application_state(self, name, message):
        self.logger.info("Setting application {} state to {}".format(name,message))
        data = { "state": message }
        self.datastore.updateApplication(name, data)

    def get_application_state(self, name):
        return self.datastore.getApplication(name)['state']

    def set_application_lock(self,name):
        return self.datastore.createApplicationLock(name)

    def remove_application_lock(self, name):
        return self.datastore.deleteApplicationLock(name)

    def get_all_urls(self):
        ab = re.compile("^.*:.*$")
        application_details = {}
        application_details['containers'] = {}
        application_details['endpoints'] = {}

        apps = self.datastore.getApplications()
        for app in apps:
            try:
                app_details = self.get(app)
                for url in app_details['urls'].split('\n'):
                    if ab.match(url):
                        (domain, location) = url.split(":")
                        if not domain in application_details['endpoints']:
                            application_details['endpoints'][domain] = {}
                        application_details['endpoints'][domain][location] = app_details['name']
                    else:
                        if not "url" in application_details['endpoints']:
                            application_details['endpoints'][url] = {}
                        application_details['endpoints'][url]['/'] = app_details['name']

                application_details['containers'][app] = app_details['containers']
            except Exception as e:
                print "Error fetching application details for urls: {}".format(e.message)

        return application_details

    def allocate_port(self):
        return self.datastore.allocatePort()

    def return_port(self, port):
        return self.datastore.releasePort(port)

