__author__ = 'unai'

import boto
from sys import argv

def attach_ebs_volume(instance_id, volume_id):
    print('Attaching volume')
    try:
        aws_client.attach_volume(volume_id, instance_id, '/dev/sdh')
    except:
        print('Could not attach volume')
        raise Exception

if __name__ == '__main__':
    print('Running')
    if len(argv) < 2:
        print('Usage: {} instance_id volume_id'.format(argv[0]))
        raise Exception
    else:
        try:
            aws_client = boto.connect_ec2()
        except:
            print('Could not connect to AWS')
            raise Exception
        instance_id = argv[1]
        volume_id = argv[2]
        attach_ebs_volume(instance_id, volume_id)