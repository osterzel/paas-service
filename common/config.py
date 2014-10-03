__author__ = 'oliver'

import os
import redis

class Config(object):
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")

        ## Assumed 16GB RAM, 128MB per container with 2-3GB reserved for OS
        self.slots_per_node = int(os.getenv("SLOTS_PER_NODE", "110"))
        self.slot_memory_mb = int(os.getenv("SLOT_MEMORY_MB", "128"))
        self.default_slots_per_instance = int(os.getenv("DEFAULT_SLOTS_PER_INSTANCE", "2"))

