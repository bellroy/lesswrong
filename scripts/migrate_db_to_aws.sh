#!/bin/bash

DB_DUMP="/tmp/db_dump_for_aws.sql.gz"

set -x

if [ `hostname` == 'serpent' ]; then
  # Dump the db
  sudo -u postgres pg_dumpall -c | gzip --rsyncable -c > $DB_DUMP

  # Sync the dump
  rsync -av $DB_DUMP root@turnip.trike.com.au:$DB_DUMP
else
  cd /srv/www/lesswrong.com/current/r2

  # Stop paster
  sudo -u www-data -H paster serve --stop-daemon --pid-file /srv/www/lesswrong.com/shared/pids/paster.pid lesswrong.com.ini

  # Extract and load the dump
  sudo -u postgres sh -c "zcat $DB_DUMP | psql -f -"

  # Restart memcache
  /etc/init.d/memcached restart

  # Start paster
  /etc/init.d/paster start
fi

set +x

