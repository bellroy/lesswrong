require 'fileutils'
require 'tempfile'
require 'pathname'
require 'shellwords'

begin
  require 'rspec/core/rake_task'
rescue LoadError
end

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
  ENV['INI'] || (r2_path + "#{environment}.ini")
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

def db_dump_prefix
  ENV['DB_DUMP_PREFIX'] || ''
end

def app_server(action)
  return unless [:start, :stop, :restart].include?(action)
  sudo "#{action} paster"
end

# These tasks assume they are running in a capistrano managed directory structure.
namespace :app do
  desc "Start the Application"
  task :start do
    app_server(:start)
  end

  desc "Stop the Application"
  task :stop do
    app_server(:stop)
  end

  desc "Restart the Application"
  task :restart do
    app_server(:restart)
  end
end

namespace :deploy do
  desc 'Run Reddit setup routine'
  task :setup do
    Dir.chdir r2_path
    sudo "python setup.py install"
    Dir.chdir basepath
    sudo "chown -R #{user} #{r2_path}"
  end

  desc "Symlink the INI files into the release path"
  task :symlink_ini do
    Dir["/usr/local/etc/reddit/#{application}.*.ini"].each do |ini|
      if File.basename(ini) =~ /#{Regexp.escape(application)}\.([^\.]+)\.ini/
        target = "#{r2_path}/#{$1}.ini"
        FileUtils.ln_sf(ini, target, :verbose => true)
      end
    end
  end

  desc 'Compress and concetenate JS and generate MD5 files'
  task :process_static_files do
    Dir.chdir r2_path
    run "./compress_js.sh"
  end

  # For compatibilty
  desc "Restart the Application"
  task :restart do
    Rake::Task['app:stop'].invoke
    Rake::Task['app:start'].invoke
  end

  desc "Copy the lesswrong crontab to /etc/cron.d in production. Requires root permissions"
  task :crontab do
    crontab = basepath + 'config' + 'crontab'
    target = "/etc/cron.d/lesswrong"
    if environment == "production"
      sudo "/bin/cp #{crontab} #{target}"
    else
      # Don't want the cron jobs running in non-production environments
      sudo "/bin/rm -f #{target}"
    end
  end

end

desc "Hook for tasks that should run after code update"
task :after_update_code => %w[
  deploy:symlink_ini
  deploy:setup
  deploy:process_static_files
  deploy:crontab
]

def conf
  @conf ||= begin
    conf = {}
    File.open(inifile.to_s) do |ini|
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


# Set the databases variable in your local deploy configuration
# expects an array of PostgreSQL database names
# Example:
#    set :databases, %w[reddit change query_queue]

namespace :postgresql do

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
    (db_dump_path + "#{db_dump_prefix}#{db}.psql").to_s.shellescape
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

namespace :memcached do
  def memcached_pid_path
    basepath + "memcached.#{environment}.pid"
  end

  task :start do
    port = conf['memcaches'].split(':').last
    pid = fork do
      exec('memcached','-p',port)
    end
    File.open(memcached_pid_path, "w") do |f|
      f.puts pid
    end
  end
  task :stop do
    pid = File.read(memcached_pid_path).to_i
    Process.kill("TERM", pid)
    File.unlink(memcached_pid_path)
  end
end

namespace :db do
  namespace :test do
    desc "Clean the test db, and re-populate it"
    task :prepare do
      ENV['APPLICATION_ENV'] = 'test'
      ENV['DATABASES'] = 'main'
      ENV['DB_DUMP_PREFIX'] = 'test-'
      Rake::Task['db:test:truncate'].invoke
      Rake::Task['postgresql:restore'].invoke
    end

    task :truncate do
      databases.each do |db|
        with_pgpass(db) do
          tables = `psql -t -A #{postgresql_opts(db)} -d #{db_conf(db, 'name')} -c "select tablename from pg_tables where schemaname='public'"`
          tables.lines.each do |table|
            run "psql #{postgresql_opts(db)} -d #{db_conf(db, 'name')} -c 'TRUNCATE TABLE #{table.chomp}'"
          end
          
          sequences = `psql -t -A #{postgresql_opts(db)} -d #{db_conf(db, 'name')} -c "select sequence_name from information_schema.sequences where sequence_schema='public'"`
          sequences.lines.each do |seq|
            run %{psql #{postgresql_opts(db)} -d #{db_conf(db, 'name')} -c "SELECT setval('#{seq.chomp}', 1, false)"}
          end

        end
      end
    end
  end
end

namespace :test do
  def paster_pid_path
    basepath + "paster.#{environment}.pid"
  end

  def paster_log_file_path
    basepath + "paster.#{environment}.log"
  end

  namespace :paster do
    task :start do
      ENV['APPLICATION_ENV'] = 'test'
      FileUtils.cd r2_path do |d|
        system(
          'paster','serve',inifile.to_s,
          '--pid-file',paster_pid_path.to_s,
          '--log-file',paster_log_file_path.to_s,
          '--daemon','--reload'
        )
      end
    end
    task :stop do
      ENV['APPLICATION_ENV'] = 'test'
      FileUtils.cd r2_path do |d|
        system('paster','serve',inifile.to_s,'--pid-file',paster_pid_path.to_s,'--stop-daemon')
      end
    end
  end

  desc "Start the server in test mode for specs"
  task :start do
    ENV['APPLICATION_ENV'] = 'test'
    Rake::Task['db:test:prepare'].invoke
    Rake::Task['memcached:start'].invoke
    Rake::Task['test:paster:start'].invoke
  end
  desc "Stop the test server"
  task :stop do
    ENV['APPLICATION_ENV'] = 'test'
    Rake::Task['test:paster:stop'].invoke
    Rake::Task['memcached:stop'].invoke
  end

  desc "Start+stop test server, and run selenium spec tests"
  task :run do
    begin
      Rake::Task['test:start'].invoke
      Rake::Task['spec:setup'].invoke
      Rake::Task['spec:test'].invoke
    ensure
      Rake::Task['test:stop'].invoke
    end
  end
end

if defined?(RSpec)
  namespace :spec do
    desc "Run the setup selenium spec"
    RSpec::Core::RakeTask.new(:setup) do |t|
      t.rspec_opts = ['--options', "\"#{basepath}/spec/spec.opts\""]
      t.pattern = 'spec/selenium-setup.rb'
    end

    desc "Run the selenium spec"
    RSpec::Core::RakeTask.new(:test) do |t|
      t.rspec_opts = ['--options', "\"#{basepath}/spec/spec.opts\""]
      t.pattern = 'spec/**/*_spec.rb'
    end
  end
end

