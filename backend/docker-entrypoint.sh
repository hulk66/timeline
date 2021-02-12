#!/bin/sh
set -e
if [ $APP = 'web' ]
  then
      ./wait
      # gunicorn -b 0.0.0.0:5000 --log-file /log/gunicorn.log --access-logfile /log/gunicorn_access.log timeline.wsgi:app
      python -m timeline.manage init
      gunicorn -b 0.0.0.0:5000 --workers=$GUNICORN_WORKERS --worker-class=$GUNICORN_WORKER_CLASS timeline.wsgi:app
elif [ $APP = 'worker' ]
  then 
      ./wait
      # fix this warning by creating proper user and group in the container
      # export C_FORCE_ROOT='true'
      # celery -A timeline.celery_main purge -f -Q beat 
      celery -A timeline.celery_all amqp queue.purge beat
      celery -A timeline.celery_all amqp queue.delete beat
      celery -A timeline.celery_all worker -P eventlet --concurrency=$THREADS -Q beat,geo_req,geo_resolve,process,face,thing,match
elif [ $APP = 'worker_process' ]
  then 
      ./wait
      # fix this warning by creating proper user and group in the container
      # export C_FORCE_ROOT='true'
      # celery -A timeline.celery_main purge -f -Q beat 
      celery -A timeline.celery_fast amqp queue.purge beat
      celery -A timeline.celery_fast amqp queue.delete beat
      celery -A timeline.celery_fast worker --concurrency=$THREADS -Q beat,geo_req,geo_resolve,process,match
elif [ $APP = 'worker_thing_face' ]
  then 
      ./wait
      # fix this warning by creating proper user and group in the container
      # export C_FORCE_ROOT='true'
      # celery -A timeline.celery_main purge -f -Q beat 
      celery -A timeline.celery_slow worker -P eventlet --concurrency=$THREADS -Q face,thing,iq

elif [ $APP = 'watchdog' ]
  then
      ./wait
      python -m timeline.manage watchdog
else
    celery -A timeline.celery_main:app flower
fi
