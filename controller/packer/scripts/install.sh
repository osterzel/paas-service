#!/bin/bash

echo "Starting the setup of a controller"

sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
apt-add-repository -y ppa:chris-lea/redis-server
echo "deb https://get.docker.com/ubuntu docker main" > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get -fy install lxc-docker redis-server rabbitmq-server
apt-get install -fy python-pip

pip install boto==2.38.0

# Move EBS scripts to their place with the right mode
mv /tmp/attach_ebs.py /usr/local/bin/attach_ebs.py
mv /tmp/mount_ebs.sh /usr/local/bin/mount_ebs.sh
mv /tmp/redis.partition /root

chmod 0755 /usr/local/bin/attach_ebs.py
chmod 0755 /usr/local/bin/mount_ebs.sh

#Change redis bind address
sed -i s/"bind 127.0.0.1"/"#bind 127.0.0.1"/g /etc/redis/redis.conf
service redis-server restart

#Setup rabbitmq
rabbitmq-plugins enable rabbitmq_management
service rabbitmq-server restart

rabbitmqctl add_vhost paas
rabbitmqctl add_user paas paas
rabbitmqctl set_permissions -p paas paas ".*" ".*" ".*"

#Setup controller docker image
git clone https://github.com/osterzel/paas-controller.git /opt/paas-controller
cd /opt/paas-controller/controller
docker build -t paas-controller .

docker create --restart=always -e RABBITMQ_URI="amqp://paas:paas@172.17.42.1:5672/paas" -e REDIS_HOST="172.17.42.1" -p 8000:8000 paas-controller
