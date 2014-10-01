__author__ = 'oliver'

from flask import g, Blueprint, render_template, jsonify
from flask.ext import restful
from .resources.applications import *
from .resources.cluster import *
from config import Config
import redis

import hashlib

api = Blueprint('api', __name__,
                     template_folder='templates', static_folder='static')


@api.before_request
def rest_initialization():
    g.config = Config()
    g.redis_conn = redis.StrictRedis(g.config.redis_host, db=1)

@api.after_request
def api_postprocessing(response):
    m = hashlib.md5()
    m.update(response.data)
    response.headers.add('Etag', m.hexdigest())
    return response

paas_api = restful.Api(api)

paas_api.add_resource(ApplicationCollection, '/app', '/app/')
paas_api.add_resource(ApplicationRecord, '/app/<string:name>')

paas_api.add_resource(ClusterCollection, '/cluster', '/cluster/')
paas_api.add_resource(ClusterRecord, '/cluster/<string:name>')

