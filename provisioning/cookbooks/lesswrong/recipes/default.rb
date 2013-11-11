require 'pathname'

%w[xml git apache2 postgresql::server postgresql::ruby database memcached-lesswrong].each { |r| include_recipe r }

%w[libyaml-dev libfreetype6-dev libjpeg62-dev libpng12-dev curl gettext
python2.7-dev python-setuptools python-imaging libevent1-dev python-geoip].each do |deb|
  package deb
end

# Directories

# Database config
postgresql_connection_info = {
  :host => node.lesswrong.db.host, :username => "postgres", :password => node['postgresql']['password']['postgres']
}

%w[reddit changes email query_queue].each do |db|
  postgresql_database_user "#{node.lesswrong.db.user}" do
    connection postgresql_connection_info
    password "#{node.lesswrong.db.password}"
    database_name db
    action :create
  end

  postgresql_database db do
    connection postgresql_connection_info
    owner "#{node.lesswrong.db.user}"
    action :create
  end
end

postgresql_database 'run script' do
  connection postgresql_connection_info
  sql { File.read(File.join(node.lesswrong.base_path, 'sql', 'functions.sql')) }
  database_name 'reddit'
  action :nothing
  subscribes :query, "cookbook_file[#{File.join(node.lesswrong.base_path, 'sql', 'functions.sql')}]", :immediately
end

template File.join(node.lesswrong.base_path, 'r2', 'development.ini') do
  source 'development.ini.erb'
  variables({
    :db_host => node.lesswrong.db.host,
    :db_user => node.lesswrong.db.user,
    :db_pass => node.lesswrong.db.password
  })
end

cookbook_file File.join(node.lesswrong.base_path, 'sql', 'functions.sql') do
  source 'functions.sql'
end

# Web config


