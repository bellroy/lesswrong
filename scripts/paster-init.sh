#!/bin/bash

DIR="/srv/www/lesswrong.com/current"
PIDFILE="/srv/www/lesswrong.com/shared/pids/paster.pid"

# This aims to set environment variables, APPLICATION, APPLICATION_USER, APPLICATION_ENV
eval $(curl --silent http://169.254.169.254/latest/user-data | grep '^export')

if [ ! -e $DIR ]; then
  echo "Directory $DIR does not exist"
  exit 1
fi

if [ ! -e $DIR/$INIFILE ]; then
  echo "INI file does not exist"
  exit 1
fi


do_start () {
  cd $DIR 
  echo "starting paster"
  rake app:start
}

do_stop () {
  echo "stopping paster"
  rake app:stop
}

do_force_stop () {
  if [ -e $PIDFILE ]; then 
    PID=`cat $PIDFILE`
    echo "killing paster with pid $PID"
    kill -9 $PID
    rm $PID
  fi
}

do_force_restart () {
  do_force_stop
  sleep 4 
  do_start
}

do_restart () {
  cd $DIR 
  echo "restarting paster"
  rake app:restart
}

case "$1" in
  start)
    do_start 
    exit 0
  ;;

  stop)
    do_stop
    exit 0
  ;;

  force-stop)
    do_force_stop
    exit 0
  ;;

  restart)
    do_restart
    exit 0
  ;;

  force-restart)
    do_force_restart
    exit 0
  ;;

  *)
    echo "Usage: $0 force-restart|force-stop|restart|start|stop" >&2
    exit 1
  ;;

esac

