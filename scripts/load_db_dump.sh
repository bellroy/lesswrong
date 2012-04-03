#!/bin/bash

for arg in "$1" "$2"; do
  if [ "EMPTY${arg}" = "EMPTY" ]; then
    echo "Usage: load_db_dump.sh basedir lesswrong.ini"
    echo "E.g. load_db_dump.sh /srv/www/lesswrong.org lesswrong.org.ini"
    exit 2
  fi
done

BASEDIR="$1"
INIFILE="$2"  # E.g. lesswrong.org.ini

first_char=`echo "$BASEDIR" | grep -o '^/'`
if [ "EMPTY${first_char}" = "EMPTY" ]; then
  echo "The basepath passed to this script must be an absolute path"
  exit 2
fi

CURRENT="$BASEDIR/current"
SHARED="$BASEDIR/shared"
APPDIR="$CURRENT/r2"

if [ ! -e "$CURRENT" ]; then
  echo "The base path doesn't appear to refer to a capistrano managed directory tree"
  exit 2
fi

DUMPFILE="$CURRENT/db/dumps/serpent.trike.com.au/production.psql.gz"
EXPORTDB="$SHARED/files/lesswrong.db"
PIDFILE="$SHARED/pids/paster.pid"

cd "$CURRENT"

# Fetch the remote production dump
cap production db:fetch_dump

cd "$APPDIR"

# Stop the current server
if [ -e "$PIDFILE" ]; then
  echo "Stopping server"
  sudo -u www-data paster serve --stop-daemon --pid-file "$PIDFILE" "$INIFILE"
fi

# Drop existing databases
for TABLE in changes email query_queue reddit; do
  sudo -u postgres dropdb "$TABLE"
done

# Extract dump
DUMPEXTRACT=`echo "$DUMPFILE" | sed s/\\.gz$//`
rm -f "$DUMPEXTRACT" # gzip will abort if the target file exists
gunzip "$DUMPFILE"

# Load dump
sudo -u postgres psql -f "$DUMPEXTRACT"

# Restart memcache as the cache is now out of date
if [ -x /etc/init.d/memcached ]; then
  sudo /etc/init.d/memcached restart
fi

# Start the server
if [ ! -e "$PIDFILE" ]; then
  echo "Starting server"
  sudo -u www-data paster serve --daemon --pid-file "$PIDFILE" "$INIFILE"
fi

# Run the export
paster run -c "export_to('${EXPORTDB}')" "$INIFILE" ../scripts/db_export.py

# Compress the export
rm -f "$EXPORTDB.bz2" # bzip2 will abort if the target file exists
bzip2 "$EXPORTDB"

# Let the group remove these files if needed (by Capistrano for example)
chmod -R g+w "$CURRENT/db"
