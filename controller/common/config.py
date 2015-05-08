__author__ = 'oliver'

import os

class Config(object):
    def __init__(self):

         #Check if we are using mysql or redis, defaults to redis
        self.datastore = os.getenv("DATASTORE", "redis")

        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))

        self.sql_address = os.getenv("SQL_ADDRESS", "sqlite:///:memory:")

        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        ## Assumed 16GB RAM, 128MB per container with 2-3GB reserved for OS
        self.slots_per_node = int(os.getenv("SLOTS_PER_NODE", "110"))
        self.slot_memory_mb = int(os.getenv("SLOT_MEMORY_MB", "128"))
        self.default_slots_per_instance = int(os.getenv("DEFAULT_SLOTS_PER_INSTANCE", "2"))

