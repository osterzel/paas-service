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

local: packerinstall .vagrantup 
	packer build -only test \
		$$(vagrant ssh-config | perl -ne 'print " -var Null$$1=$$2" if /(User|Port|HostName|IdentityFile) (\S+)/') \
                packer-template.json

.vagrantup: Vagrantfile
	vagrant up
	touch .vagrantup

ami: packerinstall
	PATH=$(PATH); packer build -only amazon-ebs packer-template.json

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
	rm -rf output
	vagrant destroy -f && rm -f .vagrantup
