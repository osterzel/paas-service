version = dev


localtest: vagrant
	venv/bin/pip install -Uqr requirements-test.txt
	. venv/bin/activate; behave

test: venv
	venv/bin/pip install -Uqr requirements-test.txt
	. venv/bin/activate; behave --tags=-dev

unittest:
	cd controller; make test
	cd router; make test

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

save-docker: controller-docker router-docker
	docker save -o controller-$(version).tgz paas-controller:$(version)
	docker save -o router-$(version).tgz paas-router:$(version)
	docker rmi paas-controller:$(version)
	docker rmi paas-router:$(version)


vagrant:
	cd paas-node; make local
	cd paas-node; vagrant ssh -c 'sudo /services/scripts/configure-services.sh $(DATASTORE)'

clean:
	cd paas-node; make clean
	rm -rf venv
