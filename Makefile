OS = $(shell uname)
ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PATH := $(ROOT_DIR)/output/packer_util:$(PATH)

ifeq ($(OS), Darwin)
        PACKER_URL = "https://dl.bintray.com/mitchellh/packer/packer_0.7.5_darwin_amd64.zip"
endif
ifeq ($(OS), Linux)
        PACKER_URL = "https://dl.bintray.com/mitchellh/packer/packer_0.7.5_linux_amd64.zip"
endif

.PHONY: clean tests

venv: venv/bin/activate 
venv/bin/activate: requirements.txt
	test -d venv || virtualenv venv
	. venv/bin/activate; pip install -Uqr requirements.txt
	touch venv/bin/activate

tests: venv
	venv/bin/pip install -Uqr requirements-tests.txt	
	test -d target || mkdir target
	. venv/bin/activate; nosetests --with-xunit --xunit-file=target/nosetests.xml --with-xcover --xcoverage-file=target/coverage/coverage.xml --cover-erase --cover-html-dir=target/coverage --cover-html --cover-package=scheduler,api,web,monitor,server

ami: packerinstall
	PATH=$(PATH); cd packer; pwd; packer build -only amazon-ebs packer-template.json

packerinstall:
ifeq ($(wildcard $(ROOT_DIR)/output/packer_util),)
	mkdir -p $(ROOT_DIR)/output
	@echo "Downloading packer"
	curl -o $(ROOT_DIR)/output/packer.zip -L $(PACKER_URL)
	unzip -o $(ROOT_DIR)/output/packer.zip -d $(ROOT_DIR)/output/packer_util
else
	@echo "Packer already downloaded"
endif

clean:
	rm -rf venv
	rm -rf target
	rm -rf packer/output
