#!/bin/bash

for arg in "$1" "$2" "$3"; do
  if [ "EMPTY${arg}" = "EMPTY" ]; then
    echo "Usage: load_db_dump.sh /path/to/dump.psql.gz /path/to/export.db lesswrong.ini"
    echo "This script should be run from within the lesswrong directory."
    echo "E.g. /srv/www/lesswrong.org/current"
    exit 2
  fi
done

DUMPFILE="$1" # E.g. /srv/www/lesswrong.org/current/db/dumps/serpent.trike.com.au/prod.psql.gz
EXPORTDB="$2" # E.g /srv/www/lesswrong.org/shared/files/lesswrong.db
INIFILE="$3"  # E.g. lesswrong.org.ini
PIDFILE="../../shared/pids/paster.pid"

# Fetch the remote production dump
cap prod db:fetch_dump

cd r2

# Stop the current server
if [ -e "$PIDFILE" ]; then
  sudo -u www-data paster serve --stop-daemon --pid-file "$PIDFILE" "$INIFILE"
fi

cd ..

# Drop existing databases
for TABLE in changes email query_queue reddit; do
  sudo -u postgres dropdb "$TABLE"
done

# Extract dump
DUMPEXTRACT=`echo "$DUMPFILE" | sed s/\\.gz$//`
rm -f "$DUMPEXTRACT" # gzip will abort if the target file exists

# Load dump
sudo -u postgres psql -f "$DUMPEXTRACT"

cd r2

# Restart memcache as the cache is now out of date
if [ -x /etc/init.d/memcached ]; then
  sudo /etc/init.d/memcached restart
fi

# Start the server
if [ -e "$PIDFILE" ]; then
  sudo -u www-data paster serve --daemon --pid-file "$PIDFILE" "$INIFILE"
fi

# Run the export
paster run -c "export_to('${EXPORTDB}')" "$INIFILE" ../scripts/db_export.py

# Compress the export
rm -f "$EXPORTDB.bz2" # bzip2 will abort if the target file exists
bzip2 "$EXPORTDB"
