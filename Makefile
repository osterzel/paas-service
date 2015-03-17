
test:
	echo "Global tests shoud go here"	

vagrant:
	vagrant up
	vagrant ssh -c 'sudo /services/scripts/configure-services.sh'
