require 'socket'
load 'config/cap-tasks/trike-aws.rb'

set :application, "lesswrong.com"
set :domains, %w[ lesswrong.com ]
set :deploy_to, "/srv/www/#{application}"
set :branch, 'staging'
set :environment, 'staging'
set :security_group, 'sg-dc5caeb3' # lesswrong-staging

set :instance, lambda {
  ami = AWS.auto_scaler_ami('lesswrong')
  raise "Unable to find ami from autoscaler" if ami.nil?

  AWS.find_or_start_host_for_security_group(
    security_group,
    ami,
    120,
    File.join('config', "user_data_#{environment}.sh.erb"),
    :instance_type => 'm1.small',
    :subnet_id => 'subnet-af1b7dc4',
    :group_ids => %w[sg-1c7d9f73 sg-267d9f49] # default server-web
  )
}

role :app, instance, :primary => true
role :web, instance, :primary => true
role :db,  "salad.trikeapps.com", :primary => true, :no_release => true

after 'multistage:ensure', :check_hostname
after 'deploy:cleanup', :check_hostname

task :check_hostname, :roles => :app, :only => :primary do
  hosts = AWS.security_group_hosts(security_group)
  unless hosts.empty?
    _, _, _, domain_ip = TCPSocket.gethostbyname(domains.first)
    _, _, _, host_ip = TCPSocket.gethostbyname(hosts.first)
    if domain_ip != host_ip
      warn "\033[31mWARNING:\033[0m #{domains.first} is not resolving to #{host_ip}. " +
        "You should add an entry to /etc/hosts:\n" +
        "#{host_ip}  #{domains.first}"
    end
  end
end

