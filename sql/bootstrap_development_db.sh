#!/bin/bash

dbs="reddit changes email query_queue"

for db in $dbs; do
    sudo -u postgres dropdb $db
#    sudo -u postgres createdb -E utf8 $db
done

sudo -u postgres psql < sql/development.sql

