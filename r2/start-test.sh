#!/bin/sh

(cd ..; export PGPASSWORD=password; ./sql/bootstrap_development_db.sh && psql -h localhost -U reddit reddit -f sql/reddit-db-test.dmp ) && sudo /etc/init.d/memcached restart && paster serve development.ini --reload port=8080
