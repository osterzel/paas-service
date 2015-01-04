__author__ = 'oliver'

import hashlib

from flask import g, Blueprint, request
from flask.ext import restful
import redis
import re

from .resources.applications import *
from .resources.globalconfig import *
from common.config import Config


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

class ApplicationCollection(restful.Resource):
    def get(self):
        return g.applications.get_all()

    def post(self):
        if not request.json:
            restful.abort(400)

        application_request = request.json
        print application_request
        try:
            application_response = g.applications.create_application(application_request)
        except Exception as e:
            restful.abort(500, message = e.message)

        return application_response, 201

class ApplicationRecord(restful.Resource):
    def get(self, name):
        try:
            return g.applications.get(name)
        except IndexError:
            restful.abort(404)

    def patch(self, name):

        if not request.json:
            restful.abort(400)

        application_request = request.json
        try:
            application_response = g.applications.update_application(name, application_request)
        except Exception as e:
            restful.abort(400, message = e.message)

        return application_response, 201

    def delete(self, name):

        return g.applications.delete_application(name)


class ApplicationUrls(restful.Resource):

    def get(self):
        #Return all the applications and url endpoints associated with them

        #This should include both subdomain and combined path based urls

        ab = re.compile("^.*:.*$")
        application_details = {}
        application_details['containers'] = {}
        application_details['endpoints'] = {}

        apps = g.redis_conn.smembers("apps")
        for app in apps:
            try:
                app_details = g.applications.get(app)
                for url in app_details['urls'].split('\n'):
                    if ab.match(url):
                        (domain, location) = url.split(":")
                        if not domain in application_details['endpoints']:
                            application_details['endpoints'][domain] = {}
                        application_details['endpoints'][domain][location] = app_details['name']
                    else:
                        if not "url" in application_details['endpoints']:
                            application_details['endpoints'][url] = {}
                        application_details['endpoints'][url]['/'] = app_details['name']

                application_details['containers'][app] = app_details['containers']
            except Exception as e:
                print "Error fetching application details for urls"

        return application_details, 201




paas_api.add_resource(ApplicationCollection, '/app', '/app/')
paas_api.add_resource(ApplicationRecord, '/app/<string:name>')
paas_api.add_resource(ApplicationUrls, '/app/urls', '/app/urls/')

class GlobalCollection(restful.Resource):
    def get(self):
        return g.global_config.get('all')

    def post(self):
        if not request.json:
            restful.abort(400)

        global_request = request.json
        try:
            global_response = g.global_config.update_environment(**global_request)
        except:
            restful.abort(400, message = "Boo")

        return global_response, 201

class GlobalRecord(restful.Resource):
    def get(self, type):
        try:
            return g.global_config.get(type)
        except:
            restful.abort(404)

    def patch(self, type = None):
        if not request.json:
            restful.abort(400)

        global_request = request.json

        try:
            global_response = g.global_config.update_environment(global_request)
        except Exception as e:
            restful.abort(400, message = e)

        return global_response, 201

paas_api.add_resource(GlobalCollection, '/global', '/global/')
paas_api.add_resource(GlobalRecord, '/global/<string:type>')

