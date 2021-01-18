#!/bin/sh
set -e
if [ $APP = 'web' ]
  then
      ./wait
      # gunicorn -b 0.0.0.0:5000 --log-file /log/gunicorn.log --access-logfile /log/gunicorn_access.log timeline.wsgi:app
      python -m timeline.manage init
      gunicorn -b 0.0.0.0:5000 timeline.wsgi:app
elif [ $APP = 'worker' ]
  then 
      ./wait
      # fix this warning by creating proper user and group in the container
      # export C_FORCE_ROOT='true'
      # celery -A timeline.celery_main purge -f -Q beat 
      celery -A timeline.celery_all amqp queue.purge beat
      celery -A timeline.celery_all worker -P eventlet --concurrency=$THREADS -Q beat,geo_req,geo_resolve,process,face,thing,match
elif [ $APP = 'init' ]
  then
      ./wait
      python -m timeline.manage init
elif [ $APP = 'watchdog' ]
  then
      ./wait
      python -m timeline.manage watchdog
elif [ $APP = 'beat' ]
  then
      ./wait
      celery -A timeline.celery_beat:app beat
else
    celery -A timeline.celery_main:app flower
fi
