__author__ = 'oliver'

from flask import g, request

from flask.ext import restful
from flask.ext.restful import reqparse
from datetime import datetime

class ClusterCollection(restful.Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type = str, required = True, help = 'No name provided', location = 'json')
        self.reqparse.add_argument('hosts', type = list, required = True, help = '{hosts} should contain a list of machines in the cluster. eg [ "127.0.0.1", "127.0.0.2" ]', location = 'json')

    def get_cluster(cluster_name):
        cluster_details = g.redis_conn.hgetall("cluster#{}".format(cluster_name))
        cluster_details['environment'] = g.redis_conn.hgetall("cluster#{}:environment".format(cluster_name))
        cluster_applications = g.redis_conn.smembers("cluster#{}:apps".format(cluster_name))
        cluster_details['applications'] = {}
        for app in cluster_applications:
            cluster_details['applications'][app] = {}
            cluster_details['applications'][app]['href'] = '/app/{}'.format(app)

        return cluster_details

    def get(self):
        clusters = list(g.redis_conn.smembers("clusters"))
        return { "data": clusters}

    def post(self):

        args = self.reqparse.parse_args()

        cluster_name = args['name']
        domain_name = args['domain_name']

        grabbed_name = g.redis_conn.hsetnx("cluster#{}".format(cluster_name), "created_at", datetime.now().isoformat())
        if not grabbed_name:
            restful.abort(400, message = "Cluster already exists")

        pipe = g.redis_conn.pipeline()
        pipe.hmset("cluster#{}".format(cluster_name), { "name": cluster_name, "domain": domain_name, "environment": { "CLUSTER_NAME": cluster_name }})
        pipe.hmset("cluster#{}:environment".format(cluster_name), { "CLUSTER_NAME": cluster_name })
        pipe.sadd("clusters", cluster_name)
        pipe.execute()

        return self.get_cluster(cluster_name)


class ClusterRecord(restful.Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('environment', type = dict, required = False, help = 'All environment variables for an application', location = 'json')

        self.reqparse.add_argument('application_config', type = dict, required = False, help = 'Application specific variables', location = 'json')

    def get(self, name):
        cluster_details = g.redis_conn.hgetall("cluster#{}".format(name))
        cluster_details['environment'] = g.redis_conn.hgetall("cluster#{}:environment".format(name))
        cluster_applications = g.redis_conn.smembers("cluster#{}:apps".format(name))
        cluster_details['applications'] = {}
        for app in cluster_applications:
            cluster_details['applications'][app] = {}
            cluster_details['applications'][app]['href'] = '/api/app/{}'.format(app)

        return cluster_details

    def delete(self, name):

        #First check if there are any applications for this cluster, if so it can't be removed
        cluster_apps = g.redis_conn.smembers("cluster#{}:apps".format(name))
        if cluster_apps:
            restful.abort(400, { "message": "Unable to remove as there are applications still running on the cluster", "applications": cluster_apps })

        pipe = g.redis_conn.pipeline()
        pipe.delete("cluster#{}".format(name))
        pipe.delete("cluster#{}:environment".format(name))
        pipe.srem("clusters", name)
        pipe.execute()

        return { "message": "cluster {} removed".format(name) }
