Vagrant.configure(2) do |config|
  config.vm.box = 'ubuntu/precise64'

  config.vm.network :forwarded_port, guest: 80, host: 8080
  config.ssh.forward_agent = true

  config.vm.provision :ansible do |ansible|
    ansible.playbook = 'provisioning/playbook.yml'
    ansible.groups = { 'vagrant' => 'default' }
    ansible.sudo = true
    ansible.verbose = 'v'
  end
end
