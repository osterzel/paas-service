#!/usr/bin/env python
__author__ = 'unai'

import boto.ec2
from sys import argv
from subprocess import call
from time import sleep


def attach_ebs_volume(instance_id, volume_id):
    print('Trying to attach volume')
    try:
        ec2.attach_volume(volume_id, instance_id, '/dev/sdh')
        print('Successfully attached volume {} to instance {}'.format(volume_id, instance_id))
        # Give it some time to become availabe
        sleep(20)
    except:
        print('Could not attach volume.')

def mount_ebs():
    print('Trying to mount EBS volume')
    try:
        call('/usr/local/bin/mount_ebs.sh')
    except:
        print('Mount failed')
        raise Exception

if __name__ == '__main__':
    print('Running')
    if len(argv) < 2:
        print('Usage: {} instance_id volume_id'.format(argv[0]))
        raise Exception
    else:
        try:
            ec2 = boto.ec2.connect_to_region('eu-west-1')
        except:
            print('Could not connect to AWS')
            raise Exception
        instance_id = argv[1]
        volume_id = argv[2]
        attach_ebs_volume(instance_id, volume_id)
        mount_ebs()