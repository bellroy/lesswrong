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

  desc 'Run Reddit setup routine'
  task :setup_reddit, :roles => :app do
    sudo "/bin/bash -c \"cd #{release_path}/r2 && python ./setup.py install\""
    sudo "/bin/bash -c \"cd #{release_path} && chown -R #{user} .\""
  end

  desc 'Compress and concetenate JS and generate MD5 files'
  task :process_static_files, :roles => :app do
    run "cd #{release_path}/r2 && ./compress_js.sh"
  end

  desc "Restart the Application"
  task :restart, :roles => :app do
    pid_file = "#{shared_path}/pids/paster.pid"
    run "cd #{current_path}/r2 && paster serve --stop-daemon --pid-file #{pid_file} #{application}.ini || true"
    run "cd #{current_path}/r2 && paster serve --daemon --pid-file #{pid_file} #{application}.ini"
  end

  desc "Update crontab"
  task :crontab, :roles => :app do
    sudo %Q{/bin/bash -c "cd #{release_path} && rake copy:cron"}
  end
end

before 'deploy:update_code', 'git:ensure_pushed'
after "deploy:update_code", "deploy:setup_reddit"
after "deploy:update_code", "deploy:process_static_files"
after "deploy:update_code", "deploy:symlink_remote_reddit_ini"
after "deploy:update_code", "deploy:crontab"
