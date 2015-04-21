# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "chef/ubuntu-14.04"
  config.vm.hostname = "webvirtmgr"
  config.vm.network "private_network", ip: "192.168.33.10"
  config.vm.provision "shell", inline: <<-SHELL
     sudo sh /vagrant/conf/libvirt-bootstrap.sh
     sudo sed -i 's/auth_tcp = \"sasl\"/auth_tcp = \"none\"/g' /etc/libvirt/libvirtd.conf
     sudo service libvirt-bin restart
     sudo apt-get -y install python-pip python-dev python-libvirt python-libxml2
     sudo pip install -r /vagrant/dev-requirements.txt
  SHELL
end
