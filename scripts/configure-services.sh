#!/bin/bash

apt-get install -fy redis-tools

CONTROLLER=`docker ps | grep controller | awk '{print $1}'`
ROUTER=`docker ps | grep router | awk '{print $1}'`
REDIS=`docker ps | grep redi | awk '{print $1}'`
RABBITMQ=`docker ps | grep rabbitmq | awk '{print $1}'`

cd /services/controller
sudo docker build -t paas-controller .

cd /services/router 
sudo docker build -t paas-router .

if [ "$REDIS" == "" ]
then
	docker run -p 6379:6379 --name redis -d redis
	sleep 2
	redis-cli sadd hosts 192.168.0.240
fi

if [ "$RABBITMQ" == "" ]
then
	RABBITMQ=`docker run -p 5672:5672 -p 15672:15672 --name rabbitmq -d tutum/rabbitmq`
	sleep 5
	#Now get password and setup rabbitmq
	USER_DETAILS=""
	while [ "$USER_DETAILS" == "" ]
	do
		USER_DETAILS=`docker logs $RABBITMQ | grep curl | awk '{print $3}'`
		sleep 2
	done
	curl -XPUT -u $USER_DETAILS -H 'Content-type: application/json' http://localhost:15672/api/users/paas -d '{ "password": "paas", "tags": "administator" }'
	curl -XPUT -u $USER_DETAILS -H 'Content-type: application/json' http://localhost:15672/api/vhosts/paas
	curl -XPUT -u $USER_DETAILS -H 'Content-type: application/json' http://localhost:15672/api/permissions/paas/paas -d '{"scope":"paas","configure":".*","write":".*","read":".*"}'
	curl -XPUT -u $USER_DETAILS -H 'Content-type: application/json' http://localhost:15672/api/permissions/paas/admin -d '{"scope":"paas","configure":".*","write":".*","read":".*"}'
	curl -XPUT -u $USER_DETAILS -H 'Content-type: application/json' http://localhost:15672/api/exchanges/paas/paas -d '{"type":"topic","auto_delete":true,"durable":true,"arguments":[]}'
	

fi

if [ "$CONTROLLER" != "" ]
then
	docker rm -f $CONTROLLER
fi
docker run -d -e RABBITMQ_URI="amqp://paas:paas@192.168.0.240:5672/paas" -e REDIS_HOST="192.168.0.240" -p 8000:8000 paas-controller

if [ "$ROUTER" != "" ]
then
	docker rm -f $ROUTER
fi
docker run -d -e RABBITMQ_URI="amqp://paas:paas@192.168.0.240:5672/paas" -p 80:80 paas-router


#Setup test slug

