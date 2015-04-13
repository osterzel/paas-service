#!/usr/bin/env python
import json
import time
import datetime
import os
import logging
from config import Config
from datastore import Redis

config = Config()

events_conn = Redis(db=2).getConnection()

def write_event(event_type, message, app_name='global'):
    try:
        # Pipeline adding to app event set and then global
        epoch_timestamp = time.time()
        count = events_conn.zcount("app#{}".format(app_name), 0, 1000000000000000000000)
        pipe = events_conn.pipeline()
        pipe.zadd("app#{}".format(app_name), epoch_timestamp, "Event: {}, Message: {}".format(event_type, message))
        if count >= 100:
            difference = count - 100
            pipe.zremrangebyrank("app#{}".format(app_name), 0, difference)
        pipe.expire("app#{}".format(app_name), 7776000)
        pipe.execute()
    except Exception as e:
        logging.error("Unable to write log event")


def get_events(app_name='all'):
    events_data = list()
    if ( app_name != "all"):
        try:
            events_data = list(events_conn.zrange("app#{}".format(app_name), 0, 100, withscores=True))
        except:
            logging.error("Unable to get list")
    else:
        pipe = events_conn.pipeline()
        keys = list(events_conn.keys("app#*"))
        if ( len(keys) > 0 ):
            pipe.zunionstore('combined', keys)
            pipe.zrange('combined', 0, -1, withscores=True)
            events_data = list(pipe.execute()[1])
        else:
            logging.error("No apps logs available")

    events_formatted = list()
    for event in events_data:
        message = event[0]
        epoch_timestamp = event[1]
        event_datestamp = datetime.datetime.fromtimestamp(epoch_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        events_formatted.append([event_datestamp, message])

    return events_formatted
