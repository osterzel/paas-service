#!/usr/bin/env python

import logging
import sys

from scheduler.maxpernode import MaxPerNodeScheduler as Scheduler
from common.applications import Applications
from common.globalconfig import GlobalConfig
from common.notifications import Notifications
from common.dockerfunctions import DockerFunctions


class ApplicationUpdater():

    def __init__(self):
        self.globalconfig = GlobalConfig()
        self.nodes = self.globalconfig.get_hosts()
        self.notifications = Notifications()
        self.application = Applications()
        self.logger = logging.getLogger(__name__)

    def process_app(self, app, number_per_node = 1, number_of_containers = 1):
        self.nodes = self.globalconfig.get_hosts()
        app_details = None
        if not self.application.set_application_lock(app):
            return False
        else:
            app_details = self.application.get(app, containers=False)
            if app_details['command'] == "":
                self.logger.debug("Command not set, application skipped")
                return False
            if app_details['docker_image'] == "":
                self.logger.debug("Docker Image not set, application skipped")
                return False

        number_per_node = 1
        number_of_containers = 1
        if "container_count" in app_details:
            try:
                if app_details['container_count'] == "all":
                    number_of_containers = len(self.nodes)
                else:
                    number_of_containers = float(app_details['container_count'])
                try:
                    number_per_node = number_of_containers / len(self.nodes)
                except ZeroDivisionError:
                    self.logger.info("No nodes, setting number_per_node to 0")
                    number_per_node = 0
            except ValueError:
                pass

        try:
            app_class = DockerFunctions(app, self.nodes, self.notifications)
            ss = Scheduler(app_class.start_instance, app_class.shutdown_instance, app_class.list_nodes, app_class.health_check, number_per_node)
            self.logger.debug("Starting scheduler for app:{}".format(app))
            output = list()
            for event in ss.run(number_of_containers):
                self.logger.debug("Scheduler Event: {}".format(event))
                output.append(event)

            self.logger.debug(output)

            self.logger.debug("Finished scheduler for app: {}".format(app))
            if ss.success == True:
                self.application.set_application_state(app, "RUNNING")
            else:
                self.application.set_application_state(app, "ERROR: {}".format(output))
        except Exception as e:
            self.logger.info("======= Scheduler Failed: {}".format(e.message))
            self.application.set_application_state(app, e.message)

        self.application.remove_application_lock(app)
        return True

