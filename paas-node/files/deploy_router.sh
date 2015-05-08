#!/bin/bash

RELEASE_NUMBER=$1
ENVIRONMENT=$2

if test "$#" -ne 2;
then
    echo "Not enough arguments"
    exit 1
fi

curl -o /tmp/router.tgz -s http://controller.${ENVIRONMENT}.mergermarket.it:9000/paas-service/${RELEASE_NUMBER}/router.tgz
docker load -i /tmp/router.tgz

rm /tmp/router.tgz

if `docker ps | grep -q router`
then
      docker rm -f router
fi

docker run -d -e RABBITMQ_URI="amqp://paas:paas@controller.${ENVIRONMENT}.mergermarket.it:5672/paas" -p 80:80 -p 8000:8000 --name router paas-router:${RELEASE_NUMBER}

docker images | grep paas-router | grep -v ${RELEASE_NUMBER} | grep -v latest | awk '{print $3}' | xargs -n 1 -r docker rmi