#!/bin/bash

dbs="reddit changes email query_queue reddit_test changes_test email_test query_queue_test"

for db in $dbs; do
    sudo -u postgres dropdb $db
    sudo -u postgres createdb -E utf8 $db
done

psql -h localhost -U reddit -d reddit < sql/functions.sql
psql -h localhost -U reddit -d reddit_test < sql/functions.sql
