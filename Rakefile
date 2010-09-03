require 'ftools'
require 'tempfile'
require 'pathname'
require 'shellwords'

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
  sudo_command = ["sudo", sudo_prompt_option, user, command].compact.join(" ")
  run sudo_command
end

def run(command)
  puts "running `#{command}'"
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

def db_dump_path
  path = basepath + "db" + "dumps"
  path.mkpath unless path.exist?
  path
end

def inifile
  ENV['INI'] || "/usr/local/etc/reddit/#{application}.#{environment}.ini"
end

def user
  ENV['APPLICATION_USER'] || raise("APPLICATION_USER environment variable must be set to run this task")
end

def application
  ENV['APPLICATION'] || raise("APPLICATION environment variable variable must be set to run this task")
end

def environment
  ENV['APPLICATION_ENV'] || raise("APPLICATION_ENV environment variable must be set to run this task")
end

def databases
  @databases ||= begin
    dbs = ENV['DATABASES'] || raise("DATABASES environment variable must be set to run this task")
    dbs.split(/\s*,\s*/)
  end
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
    sudo "paster serve --stop-daemon --pid-file #{pid_file} #{inifile} || true", :as => user
    sudo "paster serve --daemon --pid-file #{pid_file} #{inifile}", :as => user
  end

  desc "Copy the lesswrong crontab to /etc/cron.d. Requires root permissions"
  task :crontab do
    crontab = basepath + 'config' + 'crontab'
    File.copy(crontab, "/etc/cron.d/lesswrong", true)
  end
end

desc "Hook for tasks that should run after code update"
task :after_update_code => %w[deploy:setup deploy:process_static_files deploy:crontab]

# Set the databases variable in your local deploy configuration
# expects an array of PostgreSQL database names
# Example:
#    set :databases, %w[reddit change query_queue]

namespace :postgresql do

  def conf
    @conf ||= begin
      conf = {}
      File.open(inifile) do |ini|
        ini.each_line do |line|
          next if line =~ /^\s*#/ # skip comments
          next if line =~ /^\s*\[[^\]]+\]/ # skip sections

          if line =~ /\s*([^\s=]+)\s*=\s*(.*)$/
            conf[$1] = $2
          end
        end
      end
      conf
    end
  end

  def db_conf(db, var)
    key = [db, 'db', var].join('_')
    conf[key]
  end

  # Common options
  def postgresql_opts(database)
    opts = []
    opts << "--host=#{db_conf database, 'host'}"
    opts << "--username=#{db_conf database, 'user'}"
    opts << "--no-password" # Never prompt for password, its read from the file below
    opts.join(" ")
  end

  def with_pgpass(db)
    # Setup the pgpass file
    pgpass = Tempfile.new("pgpass")
    ENV['PGPASSFILE'] = pgpass.path
    pgpass.puts [
      db_conf(db, 'host'),
      '*', # port
      db_conf(db, 'name'),
      db_conf(db, 'user'),
      db_conf(db, 'pass')
    ].join(':')
    pgpass.close
    begin
      yield
    ensure
      pgpass.unlink
    end
  end

  def dump_file_path(db)
    (db_dump_path + "#{db}.psql").to_s.shellescape
  end

  desc 'Dump the database'
  task :dump do
    databases.each do |db|
      with_pgpass(db) do
        run "pg_dump #{postgresql_opts(db)} -f #{dump_file_path(db)} -Fc #{db_conf(db, 'name')}"
      end
    end
  end

  desc 'Restore the latest database dump'
  task :restore do
    databases.each do |db|
      with_pgpass(db) do
        run "pg_restore #{postgresql_opts(db)} --no-owner --clean -d #{db_conf(db, 'name')} #{dump_file_path(db)} || true"
      end
    end
  end

end

