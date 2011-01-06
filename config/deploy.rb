stages_glob = File.join(File.dirname(__FILE__), "deploy", "*.rb")
stages = Dir[stages_glob].collect { |f| File.basename(f, ".rb") }.sort
set :stages, stages

require 'capistrano/ext/multistage'
load 'config/cap-tasks/common.rb'
load 'config/cap-tasks/test.rb'
load 'config/cap-tasks/console.rb'
load 'config/cap-tasks/console.rb'
load 'config/cap-tasks/rake.rb'
load 'config/cap-tasks/postgresql_dump.rb'
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
set :databases, %w[main change email query_queue]

namespace :deploy do
  after "deploy:update_code", :roles => [:web, :app] do
    %w[files assets].each {|dir| link_shared_dir(dir) }
  end

  def rake_options
    {
      'APPLICATION' => application,
      'APPLICATION_USER' => user,
      'APPLICATION_ENV' => environment
    }.map { |k, v| "#{k}=#{v}" }.join(" ")
  end

  def link_shared_dir(dir)
    shared_subdir = "#{shared_path}/#{dir}"
    public_dir = "#{release_path}/public/#{dir}"
    run "mkdir -p #{shared_subdir}"  # make sure the shared dir exists
    run "if [ -e #{public_dir} ]; then rm -rf #{public_dir} && echo '***\n*** #{public_dir} removed (in favour of a symlink to the shared version) ***\n***'; fi"
    run "ln -sv #{shared_subdir} #{public_dir}"
  end

  desc 'Symlink all the INI files into the release dir'
  task :symlink_remote_reddit_ini, :roles => :app do
    # Not using remote rake because need to cd to release path not current
    run "cd #{release_path} && rake --trace deploy:symlink_ini #{rake_options}"
  end

  desc "Restart the Application"
  task :restart, :roles => :app do
    remote_rake "--trace deploy:restart #{rake_options}"
  end

  desc "Run after update code rake task"
  task :rake_after_update_code, :roles => :app do
    remote_rake "--trace after_update_code #{rake_options}", :path => release_path
  end
end

before 'deploy:update_code', 'git:ensure_pushed'
after "deploy:update_code", "deploy:rake_after_update_code"

