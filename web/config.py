__author__ = 'oliver'

import os

class Config(object):
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
