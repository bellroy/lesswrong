require 'pathname'

%w[xml git apache2 postgresql::server postgresql::ruby database memcached-lesswrong].each { |r| include_recipe r }
%w{mod_expires mod_proxy_http}.each { |m| include_recipe("apache2::#{m}") }

# Note, subversion is required for some of the python dependencies
%w[libyaml-dev libfreetype6-dev libjpeg62-dev libpng12-dev curl gettext
python2.7-dev python-setuptools python-imaging libevent1-dev python-geoip
subversion].each do |deb|
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

postgresql_database 'load db functions' do
  connection postgresql_connection_info
  sql { File.read '/srv/lesswrong/functions.sql' }
  database_name 'reddit'
  action :nothing
  subscribes :query, "cookbook_file[functions.sql]", :immediately
end

template File.join(node.lesswrong.base_path, 'r2', 'development.ini') do
  source 'development.ini.erb'
  variables({
    :db_host => node.lesswrong.db.host,
    :db_user => node.lesswrong.db.user,
    :db_pass => node.lesswrong.db.password,
    :wiki_host => 'staging.lwiki.trikeapps.com'
  })
end

directory '/srv/lesswrong' do
  action :create
end

cookbook_file 'functions.sql' do
  path '/srv/lesswrong/functions.sql'
end

# Python dependencies
bash 'python deps' do
  user "root"
  cwd File.join(node.lesswrong.base_path, 'r2')
  #action :nothing
  code <<-CODE
  python setup.py develop
  CODE
end

remote_file '/usr/share/GeoIP/GeoLiteCity.dat.gz' do
  source "http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz"
  action :create_if_missing
  not_if { File.exists?('/usr/share/GeoIP/GeoLiteCity.dat') }
end

bash "unzip geoip db" do
  cwd '/usr/share/GeoIP'
  code "gunzip GeoLiteCity.dat.gz && chmod 644 GeoLiteCity.dat"
  only_if { File.exists?('/usr/share/GeoIP/GeoLiteCity.dat.gz') }
end

wiki_lesswrong_xml = File.join(node.lesswrong.base_path,
                               'r2', 'r2', 'public', 'files',
                               'wiki.lesswrong.xml')
remote_file "#{wiki_lesswrong_xml}.gz" do
  source 'http://wiki.lesswrong.com/wiki.lesswrong.xml.gz'
  action :create_if_missing
  not_if { File.exists? wiki_lesswrong_xml }
end

bash 'unzip wiki.lesswrong.xml.gz' do
  cwd File.dirname(wiki_lesswrong_xml)
  code 'gunzip wiki.lesswrong.xml.gz && chmod 644 wiki.lesswrong.xml'
  only_if { File.exists? "#{wiki_lesswrong_xml}.gz" }
end

# Bootstrap the DB.
cookbook_file 'bootstrap.py' do
  path '/srv/lesswrong/bootstrap.py'
  action :create_if_missing
end

bash 'bootstrap the db' do
  cwd File.join(node.lesswrong.base_path, 'r2')
  code <<-CODE
  paster run development.ini /srv/lesswrong/bootstrap.py
  CODE
  action :nothing
  subscribes :run, 'cookbook_file[bootstrap.py]', :immediately
end

# Web config
web_app "lesswrong" do
  server_name 'lesswrong.local'
  docroot File.join(node.lesswrong.base_path, 'r2', 'r2', 'public')
  template 'apache.conf.erb'
end

apache_module 'proxy_scgi'
