#!/bin/bash -e

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
apt-get install -fy python-pip

if [ ! -x /usr/bin/pip ];
then
    apt-get update && apt-get install -xy python-pip
fi
pip install boto==2.38.0


# Move EBS scripts to their place with the right mode
mv /tmp/files/attach_ebs.py /usr/local/bin/attach_ebs.py
mv /tmp/files/mount_ebs.sh /usr/local/bin/mount_ebs.sh
mv /tmp/files/redis.partition /root

chmod 0755 /usr/local/bin/attach_ebs.py
chmod 0755 /usr/local/bin/mount_ebs.sh

adduser www-data docker

if [ -d /tmp/files ]
then
   mv /tmp/files /opt/files
fi

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
