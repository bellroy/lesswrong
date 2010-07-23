stages_glob = File.join(File.dirname(__FILE__), "deploy", "*.rb")
stages = Dir[stages_glob].collect { |f| File.basename(f, ".rb") }.sort
set :stages, stages

require 'capistrano/ext/multistage'
load 'config/cap-tasks/common.rb'
load 'config/cap-tasks/test.rb'
load 'config/cap-tasks/console.rb'
load 'config/db.rb'

set :scm, 'git'
set :repository, "git@github.com:tricycle/lesswrong.git"
set :git_enable_submodules, 1
set :deploy_via, :remote_cache
set :repository_cache, 'cached-copy'
set :engine, "paster"

# Be sure to change these in your application-specific files
set :branch, 'stable'
set :rails_env, nil
set :user, "www-data"            # defaults to the currently logged in user
set :public_path, lambda { "#{current_path}/r2/r2/public" }

namespace :deploy do
  after "deploy:update_code", :roles => [:web, :app] do
    %w[files assets].each {|dir| link_shared_dir(dir) }
  end

  def link_shared_dir(dir)
    shared_subdir = "#{shared_path}/#{dir}"
    public_dir = "#{release_path}/public/#{dir}"
    run "mkdir -p #{shared_subdir}"  # make sure the shared dir exists
    run "if [ -e #{public_dir} ]; then rm -rf #{public_dir} && echo '***\n*** #{public_dir} removed (in favour of a symlink to the shared version) ***\n***'; fi"
    run "ln -sv #{shared_subdir} #{public_dir}"
  end

  desc 'Link to a reddit ini file stored on the server (/usr/local/etc/reddit/#{application}.ini'
  task :symlink_remote_reddit_ini, :roles => :app do
    run "ln -sf /usr/local/etc/reddit/#{application}.ini #{release_path}/r2/#{application}.ini"
    if application == "lesswrong.com"
      # for backwards compatibility
      run "ln -sf /usr/local/etc/reddit/#{application}.ini #{release_path}/r2/lesswrong.org.ini"
    end
  end

  desc "Restart the Application"
  task :restart, :roles => :app do
    run %{cd #{current_path} && rake --trace deploy:restart APPLICATION_USER="#{user}" APPLICATION="#{application}"}
  end

  desc "Run after update code rake task"
  task :rake_after_update_code, :roles => :app do
    sudo %{/bin/bash -c "cd #{release_path} && rake --trace after_update_code APPLICATION_USER=\"#{user}\" APPLICATION=\"#{application}\""}
  end
end

before 'deploy:update_code', 'git:ensure_pushed'
after "deploy:update_code", "deploy:symlink_remote_reddit_ini"
after "deploy:update_code", "deploy:rake_after_update_code"

