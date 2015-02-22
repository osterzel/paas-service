#!/bin/bash

echo "Starting the setup of a controller"

sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
apt-add-repository -y ppa:chris-lea/redis-server
echo "deb https://get.docker.com/ubuntu docker main" > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get -fy install lxc-docker redis-server rabbitmq-server

#Setup rabbitmq
rabbitmq-plugins enable rabbitmq_management
service rabbitmq-server restart

rabbitmqctl add_vhost paas
rabbitmqctl add_user paas paas
rabbitmqctl set_permissions -p paas paas ".*" ".*" ".*"

#Setup controller docker image
git clone https://github.com/osterzel/paas-controller.git /opt/paas-controller
cd /opt/paas-controller
docker build -t paas-controller .

docker create --restart=always -e RABBITMQ_URL="amqp://paas:paas@172.17.42.1/paas" -p 80:8000 paas-controller
