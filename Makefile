version = dev


localtest: vagrant test

test: venv
	venv/bin/pip install -Uqr requirements-test.txt
	source venv/bin/activate; behave

venv: venv/bin/activate
venv/bin/activate: requirements.txt
	test -d venv || virtualenv venv
	. venv/bin/activate; pip install -Uqr requirements.txt
	touch venv/bin/activate

docker: controller-docker router-docker

controller-docker:
	docker build -t paas-controller:$(version) controller/.

router-docker:
	docker build -t paas-router:$(version) router/.

vagrant:
	vagrant up
	vagrant ssh -c 'sudo /services/paas-node/packer/scripts/install.sh'
	vagrant ssh -c 'sudo /services/scripts/configure-services.sh'

clean:
	vagrant destroy -f
