import sys

from flask import g, Blueprint, render_template, request
from os.path import dirname, realpath


sys.path.append(dirname(realpath(__file__)) + '../../' )

from common.paasevents import get_events
from common.datastore import Redis

from common.applications import Applications

admin_web = Blueprint('admin_web', __name__,
                     template_folder='templates', static_folder='static')

@admin_web.before_request
def rest_initialization():
     g.application = Applications()
     g.redis_conn = Redis().getConnection() 

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

    return render_template('admin/application.html', app = app, apps = apps, events = events, app_logs = [], hosts = hosts )

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
