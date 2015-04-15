#!/bin/bash

#Check if docker already installed and exit
DOCKER_EXISTS=`dpkg -l | grep lxc-docker`
if [ "$DOCKER_EXISTS" != "" ]
then
	exit 0
fi

sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
echo "deb https://get.docker.com/ubuntu docker main" > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get --force-yes -fy install lxc-docker-1.5.0 nginx

adduser www-data docker

rm -f /etc/nginx/sites-enabled/default

cat <<EOF > /etc/nginx/sites-enabled/docker.conf
upstream docker {
        server unix:///var/run/docker.sock;
}

server {
        listen 4243;
        server_name docker;

        location / {
                proxy_pass http://docker;
        }
        access_log off;
}
EOF

echo "DOCKER_OPTS=\" -H unix:///var/run/docker.sock\"" >> /etc/default/docker

service nginx restart
service docker restart
