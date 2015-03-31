import pika
import os
import logging

from config import Config


class Notifications(object):
    def __init__(self):
	self.logger = logging.getLogger(__name__)
        self.connection = None
	self.config = Config() 
        self.parameters = pika.URLParameters(os.environ.get("RABBITMQ_URI", "amqp://dev:dev@localhost:5672/paas?heartbeat=5"))
        print "RabbitMQ Url: {}".format(self.parameters)
        self.establish_connection(self.parameters)

    def establish_connection(self, parameters):
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        #self.channel.exchange_declare(exchange='paas', type='topic')
        self.logger.info("Connection established to queue-server")

    def callback(self, ch, method, properties, body):
        try:
            data = json.loads(body)
        except:
            print "Message is not in json format"

    def send_message(self, exchange, routing, body):
	self.logger.debug("Sending message to exchange:{}".format(exchange))
        try:
                self.channel.basic_publish(exchange=exchange, routing_key=routing, body=body)
        except:
                try:
                        self.establish_connection(self.parameters)
                        self.channel.basic_publish(exchange=exchange, routing_key=routing, body=body)
                except Exception as e:
                        self.logger.error("Unable to send message to queue: {}".format(e.message))

    def queue_configuration(self, queue_name, exchange, routing):

        queue_name = "router_updater_{}".format(uuid.uuid1())
        print queue_name

        #self.channel.exchange_declare("paas", "topic")
        print "Listener initializing"

        self.channel.queue_declare(queue=queue_name)
        self.channel.queue_bind(queue=queue_name, exchange=exchange, routing_key=routing)

        self.channel.basic_consume(self.callback, queue=queue_name, no_ack=False)

    def queue_listener(self, queue_name, exchange, routing):

        print "Start consuming"

        while True:
                try:
                        self.queue_configuration(queue_name, exchange, routing)
                        self.channel.start_consuming()
                except pika.exceptions.ConnectionClosed:
                        print "Connection to queue failed, retrying in 5 seconds"
                        time.sleep(5)
                        self.establish_connection(self.parameters)
