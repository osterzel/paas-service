__author__ = 'oliver'

from flask import g, Blueprint, render_template, jsonify, redirect, request, Flask
from flask.ext import restful
from .resources.applications import *
from .resources.globalconfig import *
from service import *
from config import Config
import redis

import hashlib

api = Blueprint('api', __name__,
                     template_folder='templates', static_folder='static')

@api.before_request
def rest_initialization():
    g.config = Config()
    g.global_config = GlobalConfig(Config())
    g.applications = Applications(Config())
    g.redis_conn = redis.StrictRedis(g.config.redis_host, db=0)

@api.after_request
def api_postprocessing(response):
    m = hashlib.md5()
    m.update(response.data)
    response.headers.add('Etag', m.hexdigest())
    return response

paas_api = restful.Api(api, catch_all_404s=True)

paas_api.add_resource(ApplicationCollection, '/app', '/app/')
paas_api.add_resource(ApplicationRecord, '/app/<string:name>')

paas_api.add_resource(GlobalCollection, '/global', '/global/')
paas_api.add_resource(GlobalRecord, '/global/<string:type>')

