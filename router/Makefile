.PHONY: clean tests

venv: venv/bin/activate

venv/bin/activate: requirements.txt
	test -d venv || virtualenv venv
	. venv/bin/activate; pip install -Uqr requirements.txt
	touch venv/bin/activate

tests: venv
	venv/bin/pip install -Uqr requirements-tests.txt        
	test -d target || mkdir target
	. venv/bin/activate; nosetests --with-xunit --xunit-file=target/nosetests.xml --with-xcover --xcoverage-file=target/coverage/coverage.xml --cover-erase --cover-html-dir=target/coverage --cover-html --cover-package=router,server

create-image:
	docker build -t paas-router .

clean:
	rm -rf venv
	rm -rf target


