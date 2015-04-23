#!/bin/bash

cp /tmp/files/logrotate/dockerlogs /etc/logrotate.d/

#Copy daily logrotate script to hourly as well
cp /etc/cron.daily/logrotate /etc/cron.hourly/
