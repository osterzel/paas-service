#!/usr/bin/env python

import time
import sys
import random
import uuid
import re
import logging
from common.config import Config
from common.appupdate import ApplicationUpdater
from common.config import Config
from common.datastore import Redis

def process_applications():
	config = Config()
	logging.basicConfig(level=config.log_level, format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
	#Remove verbose requests logging

	logging.getLogger("requests").setLevel(logging.WARNING)
	logging.getLogger("urllib3").setLevel(logging.WARNING)

	logger = logging.getLogger(__name__)
	redis_conn = Redis().getConnection()
	appupdate = ApplicationUpdater()

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
				logger.debug("Processing app: {}".format(app))
				output = appupdate.process_app(app)
				
		time.sleep(5)

if __name__ == '__main__':
	process_applications()
