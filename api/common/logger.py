__author__ = 'oliver'

import os
import logging

class Logger(object):

    def __init__(self, name):
        name = name.replace('.log','')
        logger = logging.getLogger('log_namespace.%s' % name)    # log_namespace can be replaced with your namespace
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            file_name = os.path.join("Stuff", '%s.log' % name)    # usually I keep the LOGGING_DIR defined in some global settings file
            handler = logging.FileHandler(file_name)
            formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s %(message)s')
            handler.setFormatter(formatter)
            handler.setLevel(logging.DEBUG)
            logger.addHandler(handler)
        self._logger = logger

    def get(self):
        return self._logger
