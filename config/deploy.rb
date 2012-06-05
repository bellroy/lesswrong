load 'config/cap-tasks/common.rb'
load 'config/cap-tasks/test.rb'
load 'config/cap-tasks/console.rb'
load 'config/cap-tasks/rake.rb'
load 'config/cap-tasks/secrets.rb'
load 'config/cap-tasks/assets.rb'
load 'config/cap-tasks/postgresql_dump.rb'
load 'config/db.rb'

stages_glob = File.join(File.dirname(__FILE__), "deploy", "*.rb")
stages = Dir[stages_glob].collect { |f| File.basename(f, ".rb") }.sort
set :stages, stages

require 'capistrano/ext/multistage'
require 'bundler/capistrano'

set :application, "lesswrong"
# This must be passed as a block, since environment is defined in the individual
# stages later.
set(:user) { "#{application}-#{environment}" }
set :scm, "git"
set :repository, 'git@github.com:tricycle/lesswrong.git'
set :repository_cache, 'cached-copy'
set :git_enable_submodules, 1
set :deploy_via, :remote_cache
set :branch, "stable" # Default branch
set :engine, "paster"
set :public_path, lambda { "#{current_path}/r2/r2/public" }
set :databases, %w[main change email query_queue]
set(:rails_env) { environment } # Used for compatibility with shared cap tasks that assume its presence

# This must be passed as a block, since environment is defined in the individual
# stages later.
set(:deploy_to) { "/srv/www/#{application}-#{environment}" }

# Secrets
set :secrets_repository, "git@git.trikeapps.com:settings/lesswrong.git"
set(:symlinked_configs) { [ "#{environment}.ini" ] }
set :bundle_without, [:development, :test]

#set :bundle_without, [:development, :test, :cucumber]

before 'deploy:update_code', 'git:ensure_pushed'

after 'deploy:update_code',  "secrets:update_configs",
                             "assets:symlink_shared_dirs",
                             "deploy:rake_after_update_code"

namespace :deploy do
  desc "Create a symlink in the release path to all _symlinked_configs_"
  task :symlink_configs do
    symlinked_configs.each do |file|
      run "ln -sf #{shared_path}/config/#{file} #{release_path}/config/#{file}"
    end
  end

  #after "deploy:update_code", :roles => [:web, :app] do
  #  %w[files assets].each {|dir| link_shared_dir(dir) }
  #end

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



