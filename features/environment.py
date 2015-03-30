from behave import *
import os
import requests
from urlparse import urlparse

def before_all(context):
    userdata = context.config.userdata

    try:
        context.slug_url = os.environ["SLUG_URL"]
    except KeyError:
        context.slug_url = userdata.get("SLUG_URL", "http://192.168.0.240:9000/testslug.tgz")

    try:
        context.api_url = os.environ['PAAS_API']
    except KeyError:
        context.api_url = userdata.get("PAAS_API", "http://192.168.0.240:8000")

    try:
        context.router_url = os.environ['ROUTER_URL']
    except KeyError:
        context.router_url  = userdata.get("ROUTER_URL", "http://192.168.0.240")

    context.web_requests = requests
