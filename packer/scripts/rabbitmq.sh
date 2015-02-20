#!/bin/bash

#Setup rabbitmq startup scripts
rabbitmq-plugins enable rabbitmq_management
service rabbitmq-server restart

rabbitmqctl add_vhost paas
rabbitmqctl add_user paas paas
rabbitmqctl set_permissions -p paas paas ".*" ".*" ".*"
