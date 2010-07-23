require 'ftools'
require 'pathname'

namespace :test do
  desc "Interactively run through the deployment test script."
  task :manual do
    # These are in here so they aren't required on the production server
    $:.unshift 'tasks/manual_test_script/lib'
    require 'active_support'
    require 'manual_test_script'
    ManualTestScript.run('test/manual.txt')
  end
end

# Borrowed from capistrano
def sudo(command, options = {})
  user = options[:as] && "-u #{options.delete(:as)}"

  sudo_prompt_option = "-p 'sudo password: '"
  sudo_command = ["sudo", sudo_prompt_option, user].compact.join(" ")
  run command
end

def run(command)
  unless system(command)
    raise RuntimeError.new("Error running command: '#{command}'")
  end
end

def basepath
  Pathname(__FILE__).dirname.realpath
end

def shared_path
   basepath.parent.parent + 'shared'
end

def r2_path
  basepath + "r2"
end

def user
  ENV['APPLICATION_USER'] || raise("APPLICATION_USER environment variable must be set to run this task")
end

def application
  ENV['APPLICATION'] || raise("APPLICATION environment variable variable must be set to run this task")
end

# These tasks assume they are running as root and will change users if necessary.
# They also assume there are running in a capistrano managed directory structure.
namespace :deploy do
  desc 'Run Reddit setup routine'
  task :setup do
    Dir.chdir r2_path
    run "python setup.py install"
    Dir.chdir basepath
    run "chown -R #{user} ."
  end

  desc 'Compress and concetenate JS and generate MD5 files'
  task :process_static_files do
    Dir.chdir r2_path
    run "./compress_js.sh"
  end

  desc "Restart the Application"
  task :restart do
    pid_file = shared_path + 'pids' + 'paster.pid'
    Dir.chdir r2_path
    sudo "paster serve --stop-daemon --pid-file #{pid_file} #{application}.ini || true", :as => user
    sudo "paster serve --daemon --pid-file #{pid_file} #{application}.ini", :as => user
  end

  desc "Copy the lesswrong crontab to /etc/cron.d. Requires root permissions"
  task :crontab do
    crontab = basepath + 'config' + 'crontab'
    File.copy(crontab, "/etc/cron.d/lesswrong", true)
  end
end

desc "Hook for tasks that should run after code update"
task :after_update_code => %w[deploy:setup deploy:process_static_files deploy:crontab]

