#!/usr/bin/env python
#author__ = 'oliver'

import os
import time
from flask import Flask, request
from flask.ext import restful
from router.config import Config
from router.notifications import Notifications
import threading

router_config = Config()

app = Flask(__name__)

notification_handler = Notifications()

class Router(restful.Resource):
    def get(self):
        return router_config.return_config()

    def post(self):
        #Call an update of the router config
        data = request.json
        return router_config.update_config(data)

router_api = restful.Api(app, catch_all_404s=True)

router_api.add_resource(Router, '/router', '/router')

if __name__ == '__main__':

    print "Starting notification handler"
    t = threading.Thread(target=notification_handler.queue_listener)
    t.daemon = True
    t.start()

    if 'PORT' in os.environ:
        port = int(os.environ.get('PORT'))
        # use '0.0.0.0' to ensure your REST API is reachable from all your
        # network (and not only your computer).
    else:
        port = 8000

    host = '0.0.0.0'

    app.run(host=host, port=port, debug=False)
