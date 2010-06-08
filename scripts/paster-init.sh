#!/bin/bash

DIR="/srv/www/lesswrong.com/current/r2"
INIFILE="lesswrong.com.ini"
PIDFILE="/srv/www/lesswrong.com/shared/pids/paster.pid"

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
  sudo -u www-data -H /usr/bin/paster serve --daemon --pid-file $PIDFILE $INIFILE
}

do_stop () {
  if [ -e $PIDFILE ]; then 
    PID=`cat $PIDFILE`
    cd $DIR 
    echo "stopping paster"
    sudo -u www-data -H /usr/bin/paster serve --stop-daemon --pid-file $PIDFILE $INIFILE 
  fi
}

do_force_stop () {
  if [ -e $PIDFILE ]; then 
    PID=`cat $PIDFILE`
    echo "killing paster with pid $PID"
    kill -9 $PID
  fi
}

do_force_restart () {
  do_force_stop
  sleep 4 
  do_start
}

do_restart () {
  do_stop
  do_start
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

