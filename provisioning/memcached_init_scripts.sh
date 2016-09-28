#!/bin/sh -e
install -m 755 -T /opt/src/memcached-lesswrong/scripts/memcached-init /etc/init.d/memcached
sed -i.bak \
    -e 's@/usr/bin/memcached@/usr/local/bin/memcached@' \
    -e 's@/usr/share/memcached/scripts/start-memcached@/usr/local/share/memcached/scripts/start-memcached@' \
    /etc/init.d/memcached
install -d -m 755 /usr/local/share/memcached/scripts
install -m 755 /opt/src/memcached-lesswrong/scripts/start-memcached /usr/local/share/memcached/scripts
sed -i.bak 's@/usr/bin/memcached@/usr/local/bin/memcached@' /usr/local/share/memcached/scripts/start-memcached
