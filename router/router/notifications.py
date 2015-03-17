__author__ = 'oliver'

import pika
import time
import os
import Queue
import json
import uuid
import threading
from config import Config

class Notifications(object):
    def __init__(self):
        self.parameters = pika.URLParameters(os.environ.get("RABBITMQ_URI", "amqp://guest:guest@localhost:5672/paas"))
	self.config_handler = Config()
	print "Initializing notification handler"
	print "Connection URL: {}".format(self.parameters)

    def callback(self, ch, method, properties, body):
        try:
            data = json.loads(body)
	    self.config_handler.update_config(data)
        except Exception as e:
	    print e
	    print e.message
	    print body 

    def establish_connection(self, parameters):
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
	print "Connected"

    def queue_configuration(self):

	queue_name = "router_updater_{}".format(uuid.uuid1())
	print queue_name

	#try:
        #	self.channel.exchange_declare("paas", "topic")
	#except:
	#	print "Exchange already declared"
        #print "Listener initializing"

        self.channel.queue_declare(queue=queue_name)
        self.channel.queue_bind(queue=queue_name, exchange="paas", routing_key='docker_container_updates')

        self.channel.basic_consume(self.callback, queue=queue_name, no_ack=True)
	print self.channel

    def queue_listener(self):
        	print "Start consuming"

		while True:
			try:
				self.establish_connection(self.parameters)
				self.queue_configuration()
       		 		self.channel.start_consuming()
			except Exception as e:
				print e.message
				print "Connection to queue failed, retrying in 5 seconds"
				time.sleep(5)
