#!/bin/sh
set -e
if [ $APP = 'web' ]
  then
      ./wait
      # gunicorn -b 0.0.0.0:5000 --log-file /log/gunicorn.log --access-logfile /log/gunicorn_access.log timeline.wsgi:app
      python -m timeline.manage db upgrade
      python -m timeline.manage init
      gunicorn -b 0.0.0.0:5000 --workers=$GUNICORN_WORKERS --worker-class=$GUNICORN_WORKER_CLASS timeline.wsgi:app
elif [ $APP = 'worker' ]
  then 
      ./wait
      # fix this warning by creating proper user and group in the container
      # export C_FORCE_ROOT='true'
      # default value if not provided - all the queues
      WORKER_QUEUES=${WORKER_QUEUES:-beat,process,analyze,geo}

      #celery -A timeline.celery_process amqp queue.purge beat
      #celery -A timeline.celery_process amqp queue.delete beat
      nice celery -A timeline.celery_process worker --autoscale=$WORKERS_PROCESS,0 -Q "${WORKER_QUEUES}"
elif [ $APP = 'transcoder' ]
  then 
      ./wait
      nice -n 20 celery -A timeline.celery_video worker --autoscale=1,0 -Q transcode_prio,transcode

elif [ $APP = 'watchdog' ]
  then
      ./wait
      nice python -m timeline.manage watchdog
else
    celery -A timeline.celery_main:app flower
fi
