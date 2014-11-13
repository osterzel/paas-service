from flask import g, Blueprint, render_template, jsonify
import redis

from os.path import dirname, realpath
import sys

sys.path.append(dirname(realpath(__file__)) + '../../' )

from common.paasevents import get_events, write_event
from common.config import Config

from api.resources.applications import Applications

admin_web = Blueprint('admin_web', __name__,
                     template_folder='templates', static_folder='static')

@admin_web.before_request
def rest_initialization():
     g.config = Config()
     g.application = Applications(g.config)
     g.redis_conn = redis.StrictRedis(g.config.redis_host, db=0)

@admin_web.route('/')
@admin_web.route('/dashboard')
def admin_dashboard():
    events = get_events()
    events.reverse()

    apps = list()
    for app in list(g.application.get_all()['data']):
        apps.append(g.application.get(app))

    sorted_apps = sorted(apps, key=lambda k: k['name'])
    print sorted_apps

    return render_template('admin/dashboard.html', events=events, apps = sorted_apps)

@admin_web.route('/application/<app_name>')
def application_admin(app_name):

    print admin_web.static_url_path

    apps = list()
    for app in list(g.application.get_all()['data']):
        apps.append(g.application.get(app))

    app = g.application.get(app_name)

    events = get_events(app_name)
    events.reverse()

    hosts = g.redis_conn.smembers("hosts")

    raw_app_logs = g.redis_conn.hgetall("app#{}:logs".format(app_name))
    for host in raw_app_logs:
        raw_app_logs[host] = raw_app_logs[host].split("\n")

    return render_template('admin/application.html', app = app, apps = apps, events = events, app_logs = raw_app_logs, hosts = hosts )

@admin_web.route("/global/", methods=["GET"])
@admin_web.route("/global", methods=["GET"])
def admin_global():
    hosts = list(g.redis_conn.smembers("hosts"))
    global_environment = g.redis_conn.hgetall("global:environment")

    return render_template('admin/global.html', hosts = hosts, global_environment = global_environment)


@admin_web.route("/events/", methods=["GET"])
@admin_web.route("/events", methods=["GET"])
def admin_logs():

    apps = list()
    for app in list(g.redis_conn.smembers("apps")):
        apps.append(g.redis_conn.hgetall("app#{}".format(app)))

    events = get_events()
    events.reverse()

    return render_template('admin/events.html', events=events, apps = apps)
