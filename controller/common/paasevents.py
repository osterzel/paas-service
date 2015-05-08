#!/usr/bin/env python
import json
import time
import datetime
import os
import logging
from config import Config
from datastore import Datastore

config = Config()

datastore = Datastore(db=2)

def write_event(event_type, message, app_name='global'):
    try:
        # Pipeline adding to app event set and then global
        epoch_timestamp = time.time()
        message = "Event: {}, Message: {}".format(event_type, message)
        datastore.writeEvent(app_name, message)
    except Exception as e:
        logging.error("Unable to write log event")


def get_events(app_name='all'):
    events_data = datastore.getEvent(app_name)

    events_formatted = list()
    for event in events_data:
        print event
        message = event[0]
        epoch_timestamp = float(event[1])
        event_datestamp = datetime.datetime.fromtimestamp(epoch_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        events_formatted.append([event_datestamp, message])

    return events_formatted
