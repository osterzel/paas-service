PAAS-Controller
=======

## What is it?

The PAAS Controller is a simplistic controller for managing a microservice cluster, it provides a web frontend and API for managing the applications and a monitoring agent to make sure the state of the cluster is maintained

#Requirements
- Python 2.7
- Redis for persistence store

#Environment variables

- REDIS_HOST (default: 127.0.0.1)

#Running it

The best way to run this is under a virtualenv

- virtualenv controller
- source controller/bin/activate
- pip install -r requirements.txt
- python server.py

## The web interface

The web interface is available on /web/

## The API

### Global endpoint

/api/global

Global variables:
```
curl /api/global/environment


### Application endpoint

/api/app/
/api/app/<app-name>


#Tests

To install a venv and run tests easily:

```
$ ./jenkins.sh
```
