__author__ = 'oliver'

from flask import g, request
from flask.ext import restful

class ApplicationCollection(restful.resource):
    def get(self):
        return g.applications.get_all()

    def post(self):
        if not request.json:
            restful.abort(400)

        application_request = request.json
        try:
            application_response = g.applications.create_application(**application_request)
        except:
            restful.abort(503)

        return application_response, 201

class ApplicationRecord(restful.resource):
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
            application_response = g.applications.update_application(name, **application_request)
        except:
            restful.abort(400)

        return application_response, 201

    def delete(self, name):
        return g.applications.delete_application(name)


class GlobalCollection(restful.resource):
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

class GlobalRecord(restful.resource):
    def get(self, type):
        try:
            return g.global_config.get(type)
        except:
            restful.abort(404)

    def post(self, type = None):
        if not request.json:
            restful.abort(400)

        global_request = restful.json

        try:
            global_response = g.global_config.update_environment(**global_request)
        except:
            restful.abort(400, message = "Boo")

        return global_response, 201

