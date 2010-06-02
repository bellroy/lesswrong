set :db_dump_filename do
  "#{stage}.psql.gz"
end

namespace :db do

  desc 'Fetches the latest PostgeSQL dump from the backup server'
  task :fetch_dump, :roles => :backups do
    host = roles[:app].servers.first.host
    source = fetch(:remote_db_dump_location, File.join(['', 'srv', 'backup', 'sql', host.sub(/\..*$/, ''), 'all_databases.psql.gz']))
    destination = fetch(:db_dump_location, File.join('db', 'dumps', host))
    unless File.directory?(destination) || File.symlink?(destination)
      FileUtils.mkdir_p destination
      File.chmod 0775, destination # Ensure group has write access
    end
    get source, File.join(destination, db_dump_filename)
  end

end
