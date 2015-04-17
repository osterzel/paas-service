#!/bin/bash

MNT_POINT='/var/lib/redis'

fdisk -l /dev/xvdh | grep -q Linux
check_disk=$?
if [ $check_disk -eq 0 ];
then
    echo 'Disk already has a partition'
else
    echo 'Need to create partition'
    sfdisk /dev/xvdh < /tmp/redis.partition
fi

if [ -d $MNT_POINT ];
then
    echo 'Mount point exists'
else
    echo 'Mount point does not exist'
    mkdir -p $MNT_POINT
fi

mount | grep -q $MNT_POINT
check_mnt=$?
if [ $check_mnt -eq 1 ];
then
    echo 'Mounting ...'
    mount -t ext4 /dev/xvdh1 $MNT_POINT
fi
