__author__ = 'oliver'

from flask import g, request

from flask.ext import restful
from flask.ext.restful import reqparse
from datetime import datetime

class ApplicationCollection(restful.Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type = str, required = True, help = 'No name provided', location = 'json')
        self.reqparse.add_argument('cluster', type = str, required = True, help = '{cluster} name not provided', location = 'json')
        self.reqparse.add_argument('command', type = str, default = ' ', help = 'Container start command', location = 'json')
        self.reqparse.add_argument('docker_image', type = str, default = ' ', location = 'json')
        self.reqparse.add_argument('environment', type = dict, default = {}, location = 'json')
        self.reqparse.add_argument('memory_in_mb', type = int, default = 256, location = 'json')
        # super(SensorCollection, self).__init__()

    def get_app(self, app_name):
        app_details = g.redis_conn.hgetall("app#{}".format(app_name))
        app_details["environment"] = g.redis_conn.hgetall("{}:environment".format(app_name))
        if app_details['cluster_name'] != None:
            app_details['global_environment'] = g.redis_conn.hgetall("cluster#{}:environment".format(app_details['cluster_name']))
        if "memory_in_mb" in app_details:
            app_details["memory_in_mb"] = int(app_details["memory_in_mb"])
        if not app_details:
            restful.abort(404, message = "No details found")
        return app_details


    def get(self):
        applications = list(g.redis_conn.smembers("apps"))
        return { "data": applications }

    def post(self):
        args = self.reqparse.parse_args()

        if not g.redis_conn.exists("ports"):
            paas_init_lock = g.redis_conn.execute_command("SET", "initlock", "locked", "NX", "EX", "60")
            if not paas_init_lock:
                restful.abort(500, message = "tried to init app but it looks like someone else already is")
            g.redis_conn.sadd("ports", *range(49152, 65535))

        name = args['name']
        cluster_name = args['cluster']

        #Test to see if cluster exists
        cluster_record = g.redis_conn.hgetall("cluster#{}".format(cluster_name))
        if cluster_record == None:
            cluster_name = None

        grabbed_name = g.redis_conn.hsetnx("app#{}".format(name), "created_at", datetime.now().isoformat())
        if not grabbed_name:
            restful.abort(400, message = "app already exists")
        port = g.redis_conn.spop("ports")
        if not port:
            g.redis_conn.delete("app#{}".format(name))
            restful.abort(400, message = "no free ports, likely you forgot to init")

        pipe = g.redis_conn.pipeline()
        pipe.hmset("app#{}".format(name),
            {
                "name": name, "port": port, "ssl": "false", "ssl_certificate_name": "", "docker_image": "", "state": "virgin", "memory_in_mb": 512, "command": "", "cluster_name": cluster_name})
        pipe.rpush("monitor", name)
        pipe.sadd("apps", name)
        if cluster_name != None:
            pipe.sadd("cluster#{}:apps".format(cluster_name), name)
        pipe.execute()
        #write_event("CREATE APP", "Create app - {}".format(app_name), app_name)
        return self.get_app(name)




class ApplicationRecord(restful.Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('environment', type = dict, required = False, help = 'All environment variables for an application', location = 'json')
        self.reqparse.add_argument('cluster', type = str, required = False, help = 'Cluster name', location = 'json')

    def get(self, name):
        app_details = g.redis_conn.hgetall("app#{}".format(name))
        if not app_details:
            restful.abort(400, message = "Application not found")

        app_details["environment"] = g.redis_conn.hgetall("{}:environment".format(name))
        print app_details
        if "cluster_name" in app_details:
            if app_details['cluster_name'] != None:
                app_details['global_environment'] = g.redis_conn.hgetall("cluster#{}:environment".format(app_details['cluster_name']))

        if "memory_in_mb" in app_details:
            app_details["memory_in_mb"] = int(app_details["memory_in_mb"])
        if not app_details:
            restful.abort(404, message = "Application not found")

        return app_details

    def patch(self, name):
        if not g.redis_conn.exists("app#{}".format(name)):
            restful.abort(404, message = "Application not found")
        if g.redis_conn.hget("app#{}".format(name), "state") == "deleting":
            restful.abort(400, message = "in deleting state")
        pipe = g.redis_conn.pipeline()
        if "restart" in request.json:
            environments = g.redis_conn.hgetall("{}:environment".format(name))
            try:
                new_counter = int(environments['RESTART']) + 1
            except KeyError:
                new_counter = 1

        if not request.json.has_key('environment'):
            request.json['environment'] = {}
            request.json['environment']['RESTART'] = int(1)

        #write_event("UPDATED APP", "App {}, restart called".format(app_name), app_name)

        if "cluster_name" in request.json:
            current_cluster = g.redis_conn.hget("app#{}".format(name), "cluster_name")

            if ( current_cluster != request.json['cluster_name'] ) and current_cluster != None:
                pipe.srem("cluster#{}:apps".format(current_cluster), name)
            #Test to see if cluster exists
            cluster_record = g.redis_conn.hgetall("cluster#{}".format(request.json['cluster_name']))
            if cluster_record != None:
                pipe.hset("app#{}".format(name), "cluster_name", request.json['cluster_name'])
                pipe.sadd("cluster#{}:apps".format(request.json['cluster_name']))

        if "ssl" in request.json:
            pipe.hset("app#{}".format(name), "ssl", request.json["ssl"])
        if "ssl_certificate_name" in request.json:
            pipe.hset("app#{}".format(name), "ssl_certificate_name", request.json["ssl_certificate_name"])
        if "memory_in_mb" in request.json:
            pipe.hset("app#{}".format(name), "memory_in_mb", request.json["memory_in_mb"])
        else:
            pipe.hsetnx("app#{}".format(name), "memory_in_mb", 0)
        if "docker_image" in request.json:
            pipe.hset("app#{}".format(name), "docker_image", request.json["docker_image"])
        if "command" in request.json:
            pipe.hset("app#{}".format(name), "command", request.json["command"])
        if "environment" in request.json:
            if "PORT" in request.json["environment"].keys():
                restful.abort(400, message = "trying to set PORT, nice try but no cigaar")
            to_set = {k:v for k,v in request.json["environment"].items() if v}
            if to_set:
                pipe.hmset("{}:environment".format(name), to_set)
            to_remove = [k for k,v in request.json["environment"].items() if not v ]
            if to_remove:
                pipe.hdel("{}:environment".format(name), *to_remove)
        pipe.hset("app#{}".format(name), "state", "OUT OF DATE, AWAITING DEPLOY")
        pipe.execute()
        #write_event("UPDATED APP", "App {} was updated".format(name), name)
        return self.get(name)



    def delete(self, name):

        if not g.redis_conn.exists("app#{}".format(name)):
            restful.abort(400, message = "app does not exist")

        port = g.redis_conn.hget("app#{}".format(name), "port")

        pipe = g.redis_conn.pipeline()
        cluster = g.redis_conn.hget("app#{}".format(name), "cluster_name")
        if cluster != None:
            pipe.srem("cluster#{}:apps", name)

        pipe.delete("app#{}".format(name))
        pipe.delete("{}:environment".format(name))
        pipe.lrem("monitor", 0, name)
        pipe.srem("apps", name)
        pipe.sadd("ports", port)
        pipe.execute()

        #write_event("DELETE APP", "Deleted app - {}".format(name), name)
        return { "message": "Application deleted", "app_port": port}
