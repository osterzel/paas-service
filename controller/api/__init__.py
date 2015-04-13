__author__ = 'oliver'

import hashlib
import sys

from flask import g, Blueprint, request, json
from flask.ext import restful
from os.path import dirname, realpath


sys.path.append(dirname(realpath(__file__)) + '../' )

from common.applications import *
from common.globalconfig import *
from common.datastore import Redis
try:
	from common.appupdate import ApplicationUpdater
except:
	pass

api = Blueprint('api', __name__,
                     template_folder='templates', static_folder='static')

@api.before_request
def rest_initialization():
    g.global_config = GlobalConfig()
    g.applications = Applications()
    g.redis_conn = Redis().getConnection()

@api.after_request
def api_postprocessing(response):
    m = hashlib.md5()
    m.update(response.data)
    response.headers.add('Etag', m.hexdigest())
    return response

paas_api = restful.Api(api, default_mediatype = 'application/json', catch_all_404s=True)

def validate_json(request):
        if request.headers['Content-type'] != 'application/json':
            restful.abort(400, message = 'Content-type must be application/json')

        try:
            json.dumps(request.json)
        except Exception as e:
            restful.abort(400, message = 'Not valid json, {}'.format(request.data))

class ApplicationCollection(restful.Resource):
    def get(self):
        return g.applications.get_all()

    def post(self):
        validate_json(request)

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

        validate_json(request)
        application_request = request.json
        try:
            application_response = g.applications.update_application(name, application_request)
        except Exception as e:
            restful.abort(500, message = e.message)

	if request.args.get('synchronous'):
    		appupdater = ApplicationUpdater()
        	appupdater.process_app(name)
		application_response = g.applications.get(name)

        return application_response, 201

    def delete(self, name):

        return g.applications.delete_application(name)

class ApplicationUrls(restful.Resource):

    def get(self):
        #Return all the applications and url endpoints associated with them

        #This should include both subdomain and combined path based urls

        application_details = g.applications.get_all_urls()

        return application_details, 201



paas_api.add_resource(ApplicationCollection, '/app', '/app/')
paas_api.add_resource(ApplicationRecord, '/app/<string:name>')
paas_api.add_resource(ApplicationUrls, '/app/urls', '/app/urls/')

class HostCollection(restful.Resource):
    def get(self):
        return g.global_config.get_hosts()

    def post(self):
        if not request.json:
            restful.abort(400)

        global_request = request.json
        try:
            global_response = g.global_config.add_host(global_request)
        except:
            restful.abort(400, message = "Boo")

        return global_response, 201

class HostRecord(restful.Resource):
    def get(self, host):
        try:
            return g.global_config.get_host(host)
        except:
            restful.abort(404)

paas_api.add_resource(HostCollection, '/global/hosts', '/global/hosts/')
paas_api.add_resource(HostRecord, '/global/hosts/<string:type>')

