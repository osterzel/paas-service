box        = 'trusty64'
url        = 'https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-clou
dimg-amd64-vagrant-disk1.box'
hostname   = 'paas'
domain     = 'testing.com'
ip_address = '192.168.0.240'
ram        = '1024'

Vagrant.configure("2") do |config|
  config.vm.box = box
  config.vm.box_url = url
  config.vm.hostname = hostname + '.' + domain
  config.vm.network "private_network", ip: ip_address
  config.vm.synced_folder ".", "/services"

  config.vm.provider "virtualbox" do |vb|
    vb.customize [
      'modifyvm', :id,
      '--name', hostname,
      '--memory', ram
    ]
  end

  config.vm.provision "shell", path: "scripts/docker_install.sh"

end
