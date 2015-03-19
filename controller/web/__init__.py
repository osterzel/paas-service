import sys

from flask import g, Blueprint, render_template, request
import redis
from os.path import dirname, realpath


sys.path.append(dirname(realpath(__file__)) + '../../' )

from common.paasevents import get_events
from common.config import Config

from common.applications import Applications

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

    search_string = None
    if request.args.get('search'):
        search_string = request.args.get('search')
    else:
        search_string = ""

    apps = list()
    for app in list(g.application.get_all()['data']):
        if search_string in app:
            apps.append(g.application.get(app, containers = False))

    sorted_apps = sorted(apps, key=lambda k: k['name'])

    return render_template('admin/dashboard.html', events=events, apps = sorted_apps, search_string = search_string)

@admin_web.route('/application/<app_name>')
def application_admin(app_name):

    print admin_web.static_url_path

    apps = list()
    for app in list(g.application.get_all()['data']):
        apps.append(g.application.get(app, containers = False))

    try:
        app = g.application.get(app_name, containers = True)
    except Exception:
        app = {}

    events = get_events(app_name)
    events.reverse()

    hosts = g.redis_conn.smembers("hosts")
    raw_app_logs = g.application.get_container_logs(app_name)
    app_logs = []
    #Make sure strings are unicode
    for logentry in raw_app_logs:
       app_logs.append(unicode(logentry, 'utf8'))

    #for host in raw_app_logs:
    #    raw_app_logs[host] = raw_app_logs[host].split("\n")

    return render_template('admin/application.html', app = app, apps = apps, events = events, app_logs = app_logs, hosts = hosts )

@admin_web.route("/global/", methods=["GET"])
@admin_web.route("/global", methods=["GET"])
def admin_global():
    hosts = list(g.redis_conn.smembers("hosts"))

    return render_template('admin/global.html', hosts = hosts)

@admin_web.route("/events/", methods=["GET"])
@admin_web.route("/events", methods=["GET"])
def admin_logs():

    apps = list()
    for app in list(g.redis_conn.smembers("apps")):
        apps.append(g.redis_conn.hgetall("app#{}".format(app)))

    events = get_events()
    events.reverse()

    return render_template('admin/events.html', events=events, apps = apps)
