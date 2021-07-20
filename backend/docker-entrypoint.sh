#!/bin/sh
set -e
if [ $APP = 'web' ]
  then
      ./wait
      # gunicorn -b 0.0.0.0:5000 --log-file /log/gunicorn.log --access-logfile /log/gunicorn_access.log timeline.wsgi:app
      python -m timeline.manage init
      gunicorn -b 0.0.0.0:5000 --workers=$GUNICORN_WORKERS --worker-class=$GUNICORN_WORKER_CLASS timeline.wsgi:app
elif [ $APP = 'worker_process' ]
  then 
      ./wait
      # fix this warning by creating proper user and group in the container
      # export C_FORCE_ROOT='true'
      # celery -A timeline.celery_main purge -f -Q beat 
      celery -A timeline.celery_process amqp queue.purge beat
      celery -A timeline.celery_process amqp queue.delete beat
      celery -A timeline.celery_process worker --autoscale=$WORKERS_PROCESS,0 -Q beat,process
elif [ $APP = 'worker_analyze' ]
  then 
      ./wait
      celery -A timeline.celery_analyze worker --concurrency=$WORKERS_ANALYZE -Q analyze

elif [ $APP = 'watchdog' ]
  then
      ./wait
      python -m timeline.manage watchdog
else
    celery -A timeline.celery_main:app flower
fi
