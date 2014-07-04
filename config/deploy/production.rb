load 'config/cap-tasks/trike-aws.rb'

set :application, "lesswrong.com"
set :domains, %w[ lesswrong.com ]
set :elb_name, 'lblw'
set :hosts, lambda { AWS.elb_hosts(elb_name) }
set :environment, 'production'

set :primary_host, hosts.shift

role :app, primary_host, :primary => true
role :app, *hosts
role :web, primary_host, :primary => true
role :web, *hosts
role :db,  "salad.trikeapps.com", :primary => true, :no_release => true
role :backups, "backup.trikeapps.com", :user => 'backup', :no_release => true

before "deploy:update_code", "tests_check:manual_tests_executed?"
after 'deploy:update_code', 'git:tag_deploy'

# XXX: Disabled for now - it fails to remove the 20110705001432
# release. Fix when we cut the next AMI.
# after 'deploy:restart', 'deploy:cleanup'

after 'multistage:ensure', :check_hostname
after 'deploy:cleanup', :check_hostname

task :check_hostname, :roles => :app, :only => :primary do
  balancers = AWS.elb.describe_load_balancers(elb_name)
  unless balancers.empty?
    domain = domains.first
    balancer = balancers.first
    _, _, _, domain_ip = TCPSocket.gethostbyname(domain)
    _, _, _, balancer_ip = TCPSocket.gethostbyname(balancer[:dns_name])
    if domain_ip != balancer_ip
      warn "\033[31mWARNING:\033[0m #{domain} is not resolving to the IP for the #{elb_name} elb.\n" +
        "Do you have an entry in /etc/hosts that needs removing?"
    end
  end
end
