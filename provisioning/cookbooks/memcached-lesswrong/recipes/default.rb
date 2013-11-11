#
# Cookbook Name:: memcached
# Recipe:: default

package "libevent1-dev" do
  action :upgrade
end

package "memcached" do
  action :purge
end

git "/srv/memcached" do
  repository "https://github.com/tricycle/memcached.git"
  reference "master"
  action :sync
  notifies :run, "bash[install_memcached]"
end

bash "install_memcached_start_scripts" do
  user "root"
  cwd "/tmp"
  action :nothing
  code <<-EOH
  cp /srv/memcached/scripts/memcached-init /etc/init.d/memcached
  update-rc.d memcached defaults
  sed -i.bak 's@/usr/bin/memcached@/usr/local/bin/memcached@' /etc/init.d/memcached
  mkdir -p /usr/share/memcached/scripts
  cp /srv/memcached/scripts/start-memcached /usr/share/memcached/scripts/start-memcached
  sed -i.bak 's@/usr/bin/memcached@/usr/local/bin/memcached@' /usr/share/memcached/scripts/start-memcached
  EOH
end

bash "install_memcached" do
  user "root"
  cwd "/srv/memcached"
  action :nothing
  notifies :run, "bash[install_memcached_start_scripts]", :immediately
  code <<-EOH
  (cd /srv/memcached/ && ./configure )
  (cd /srv/memcached/ && make && make install)
  EOH
end

service "memcached" do
  action :nothing
  supports :status => true, :start => true, :stop => true, :restart => true
end

template "/etc/memcached.conf" do
  source "memcached.conf.erb"
  owner "root"
  group "root"
  mode "0644"
  variables(
    :listen => node[:memcached][:listen],
    :user => node[:memcached][:user],
    :port => node[:memcached][:port],
    :maxconn => node[:memcached][:maxconn],
    :memory => node[:memcached][:memory]
  )
  notifies :restart, resources(:service => "memcached"), :immediately
end
