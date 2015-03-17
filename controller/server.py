__author__ = 'oliver'

import os
from flask import Flask
from web import admin_web
from api import api

app = Flask(__name__)

app.register_blueprint(admin_web, url_prefix='/web')
app.register_blueprint(api, url_prefix='')


if __name__ == '__main__':
    if 'PORT' in os.environ:
        port = int(os.environ.get('PORT'))
        # use '0.0.0.0' to ensure your REST API is reachable from all your
        # network (and not only your computer).
    else:
        port = 8000

    host = '0.0.0.0'

    app.run(host=host, port=port, debug=False)
