
test:
	echo "Global tests shoud go here"	

vagrant:
	vagrant up
	vagrant ssh -c 'sudo /services/paas-node/packer/scripts/install.sh'
	vagrant ssh -c 'sudo /services/scripts/configure-services.sh'

clean:
	vagrant destroy -f
