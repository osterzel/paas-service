__author__ = 'oliver'

import redis
import json
import couchdb

class RedisDataAccess():

    def __init__(self, host):
        self.redis_conn = redis.StrictRedis(host, db = 1)

    def get_set(self, id):
        data = []
        for key in self.redis_conn.keys(id):
            data.append(self.redis_conn.smembers(key))

    def get_records(self, id):
        data = {}
        for key in self.redis_conn.keys(id):
            data[key] = {}
            data[key] = (self.redis_conn.hgetall(key))
        return data

    def get_record(self, id):
        return self.redis_conn.hgetall(id)


    def save_record(self, id, data):
        to_set = {k:v for k,v in data.items() if v}
        return self.redis_conn.hmset(id, to_set)

    def delete_record(self, id):
        return self.redis_conn.delete(id)

    def get_data_object(self):
        return self.redis_conn

