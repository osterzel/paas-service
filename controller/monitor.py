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
from common.datastore import Datastore

def process_applications():
	config = Config()
	logging.basicConfig(level=config.log_level, format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
	#Remove verbose requests logging

	logging.getLogger("requests").setLevel(logging.WARNING)
	logging.getLogger("urllib3").setLevel(logging.WARNING)

	logger = logging.getLogger(__name__)
	datastore = Datastore()
	appupdate = ApplicationUpdater()

	while True:
		apps = datastore.getApplications()
		print apps
		for app in apps: 
				logger.debug("Processing app: {}".format(app))
				output = appupdate.process_app(app)
				
		time.sleep(5)

if __name__ == '__main__':
	process_applications()
