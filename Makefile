
test:
	echo "Global tests shoud go here"	

vagrant:
	vagrant up
	vagrant ssh -c 'cd /services/controller; docker build -t paas-controller .'
	vagrant ssh -c 'cd /services/router; docker build -t paas-router .'
	vagrant ssh -c 'docker run -p 6379:6379 redis'
	vagrant ssh -c 'docker run -p 5672:5672 -p 15672:15672 tutum/rabbitmq'
