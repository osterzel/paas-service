#!/usr/bin/env python

__author__ = 'unai'

from boto import ec2
import requests
from sys import argv

if len(argv) <= 2:
    print('usage: {} environment mode'. format(argv[0]))
    raise KeyError
environment = argv[1]
mode = argv[2]

controller = 'http://controller.{}.mergermarket.it:8000'.format(
    environment
)
# controller = 'http://localhost:8000'
hosts_endpoint = '/global/hosts'

allowed_modes = ['client', 'update']
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

def get_current_hosts():
    try:
        r = requests.get('{}/{}'.format(controller,
                                        hosts_endpoint))
    except Exception as e:
        print('Could not get hosts. Got {}'.format(e.message
                                                   ))
        raise Exception
    return r.json()

current_members = get_current_hosts()
running = get_instance_ips()
news = set(running).difference(current_members)
old = set(current_members).difference(running)

def add_all_members():
    hosts = {"hosts": []}
    for t in news:
        hosts['hosts'].append(t)
    if len(news) > 0:
        print("Adding: {}".format(news))
        try:
            a = requests.post('{}{}'.format(controller, hosts_endpoint),json=hosts)
        except Exception as e:
            print('Failed to update hosts: {}'.format(e.message))
        print('Server says: {}'.format(a.text))
    else:
        print('Nothing to add')

def remove_old_members():
    hosts = {"hosts": []}
    for t in old:
        hosts['hosts'].append(t)
    if len(old) > 0:
        print("Removing: {}".format(old))
        try:
            d = requests.delete('{}{}'.format(controller, hosts_endpoint),json=hosts)
        except Exception as e:
            print('Failed to update hosts: {}'.format(e.message))
        print('Server says: {}'.format(d.text))
    else:
        print('Nothing to remove')

if __name__ == '__main__':
    if mode == 'client':
        print(' '.join(running))
    if mode == 'update':
        remove_old_members()
        add_all_members()