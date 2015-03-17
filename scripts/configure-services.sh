#!/bin/bash

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
fi

if [ "$RABBITMQ" == "" ]
then
	docker run -p 5672:5672 -p 15672:15672 --name rabbitmq -d tutum/rabbitmq
	#Now get password and setup rabbitmq
fi

if [ "$CONTROLLER" != "" ]
then
	docker rm -f $CONTROLLER
fi
docker run -d -e RABBITMQ_URI="amqp://paas:paas@192.168.0.240:5672/paas" -e REDIS_HOST="192.168.0.240" paas-controller

if [ "$ROUTER" != "" ]
then
	docker rm -f $ROUTER
fi
docker run -d -e RABBITMQ_URI="amqp://paas:paas@192.168.0.240:5672/paas" paas-router

