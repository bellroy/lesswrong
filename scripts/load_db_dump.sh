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
paster serve --stop-daemon --pid-file "$PIDFILE" "$INIFILE"

cd ..

# Drop existing databases
for TABLE in changes email query_queue reddit; do
  sudo -u postgres dropdb "$TABLE"
done

# Extract and load
sudo -u postgres sh -c "gunzip -c \"$DUMPFILE\" | psql"

cd r2

# Stop the current server
paster serve --daemon --pid-file "$PIDFILE" "$INIFILE"

# Run the export
paster run -c "export_to('${EXPORTDB}')" "$INIFILE" ../scripts/db_export.py

# Compress the export
rm -f "$EXPORTDB.bz2" # bzip2 will exit if the target file exists
bzip2 "$EXPORTDB"
