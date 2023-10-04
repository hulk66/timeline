FROM hulk66/timeline_be_base:0.96

COPY . /tmp/myapp
RUN pip install /tmp/myapp

WORKDIR /tmp/myapp
COPY envs/env.docker .env

ENTRYPOINT ["/tmp/myapp/docker-entrypoint.sh"]
