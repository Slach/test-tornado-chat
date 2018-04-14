# -*- mode: ruby -*-
# vi: set ft=ruby :
Vagrant.configure(2) do |config|
	config.vm.box = "ubuntu/xenial64"
	config.vm.box_check_update = false

	config.hostmanager.enabled = true
	config.hostmanager.manage_host = true
	config.hostmanager.ignore_private_ip = false
	config.hostmanager.include_offline = false

	config.vm.provider "virtualbox" do |vb|
		vb.gui = false
		vb.memory = "512"
		vb.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/vagrant", "1"]
	end

	config.vm.define :chatserver_develop do |chatserver_develop|
		chatserver_develop.vm.host_name = "vagrant-test-tornado-chatserer"
		chatserver_develop.hostmanager.aliases = ["vagrant.test.tornado.chatserver"]
		chatserver_develop.vm.network "private_network", ip: "172.16.2.89"
 		chatserver_develop.vm.provision "shell", inline: <<-SHELL
			set -xeuo pipefail
			echo 'APT::Periodic::Enable "0";' > /etc/apt/apt.conf.d/02periodic
			apt update
			apt install -y apt-transport-https software-properties-common
			# docker
			apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 8D81803C0EBFCD88
			add-apt-repository "deb https://download.docker.com/linux/ubuntu xenial edge"
			apt update
			apt install -y docker-ce
			apt install -y python-pip
			pip install -U pip
			pip install -U docker-compose

			set +x

			echo "chatserver_develop VAGRANT PROVISIONING DONE, use following scenario for developing"
			echo "#  vagrant ssh chatserver_develop"
			echo "#  sudo bash -c \\\"cd /vagrant && ./run_docker.sh\\\""
			echo "#  open http://vagrant.test.tornado.chatserver/"
			echo "Good Luck ;)"
		SHELL
	end

end
