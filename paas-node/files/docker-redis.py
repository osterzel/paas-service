#!/usr/bin/env python

__author__ = 'unai'

from boto import ec2, utils
import redis
from sys import argv


if len(argv) <= 2:
    print('usage: {} environment mode'. format(argv[0]))
    raise KeyError
environment = argv[1]
mode = argv[2]

allowed_modes = ['self', 'controller', 'client']
if mode not in allowed_modes:
    print('mode not allowed')
    raise KeyError


def get_instance_ips():

    conn = ec2.connect_to_region('eu-west-1')
    tag_name = '{} PaaS-dockerhosts'.format(environment)
    reservations = conn.get_all_instances(filters={'tag:Name': tag_name, 'instance-state-name': 'running'})
    all_instances = [instance for reservation in reservations for instance in reservation.instances]

    instance_ips = []
    for instance in all_instances:
        instance_ips.append(instance.__dict__['private_ip_address'])
    return instance_ips


def get_instance_ip():
    return utils.get_instance_metadata()['local-ipv4']

redis_host = 'controller.{}.mergermarket.it'.format(environment)
r = redis.StrictRedis(redis_host, db=0)
current_members = r.smembers('hosts')
running = get_instance_ips()


def add_member():
    if not r.sismember('hosts', get_instance_ip()):
        print('Add member')
        r.sadd('hosts', get_instance_ip())
    else:
        print('Already a member')


def remove_old_members():
    olds = set(current_members).difference(running)
    for to_remove in olds:
        print('Delete node {}'.format(to_remove))
        r.srem('hosts', to_remove)


def add_all_members():
        news = set(running).difference(current_members)
        for to_add in news:
            print('Adding member {}'.format(to_add))
            r.sadd('hosts', to_add)

if __name__ == '__main__':
    if mode == 'controller':
        add_all_members()
    if mode == 'self':
        add_member()
        remove_old_members()
    if mode == 'client':
        print(' '.join(get_instance_ips()))