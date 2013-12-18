#!/bin/sh
# Run from the r2 directory, like `../scripts/db_export.sh lesswrong.sqlite`

if [ -z "$1" ]; then
    echo 'Usage: ../db_export.sh DBNAME'
    exit 1
fi

for feature in users links comments votes indexes; do
    paster run production.ini ../scripts/db_export.py -c "export_to('$1', ['$feature'])"
done
