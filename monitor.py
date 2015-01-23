#!/usr/bin/env python

from scheduler.maxpernode import MaxPerNodeScheduler as Scheduler
import docker
import redis
import time
import sys
import random
import uuid
import re
from common.logger import ConsoleLogger
from common.dockerfunctions import DockerFunctions
from common.config import Config
from api.resources.applications import Applications
from api.resources.globalconfig import GlobalConfig
from common.notifications import Notifications

def process_applications():
	config = Config()
	redis_conn = redis.StrictRedis(config.redis_host)
	globalconfig = GlobalConfig(config)
	nodes = globalconfig.get('hosts')
	notifications = Notifications(config)
	application = Applications(config)
	while True:
		apps = redis_conn.lrange('monitor', 0, -1)
		#apps = [ "ci-trend-admin", "courtdocs.daemon.ci" ]
		redis_apps = redis_conn.keys("app#*")
		apps = []
		for redis_app in redis_apps:
			if not ":" in redis_app:
				name = redis_app.split('#')[1]
				apps.append(name)
		for app in apps: 
				print app
				if not application.set_application_lock(app):
					continue
				else:
					print app

				try:
					app_class = DockerFunctions(app, nodes, config, notifications)
					ss = Scheduler(app_class.start_instance, app_class.shutdown_instance, app_class.list_nodes, app_class.health_check, 1)
					print "Starting scheduler"
					output = list(ss.run(1))
					print "Finished scheduler"
					print output
					if ss.success == True:
						application.set_application_state(app, "RUNNING")
					else:
						application.set_application_state(app, "ERROR: Problem deploying application, {}".format(output))
				except Exception as e:
					print "======= Scheduler Failed"
					application.set_application_state(app, e.message)
				application.remove_application_lock(app)
		time.sleep(10)

if __name__ == '__main__':
	process_applications()
