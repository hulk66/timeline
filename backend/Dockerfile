FROM python:3.8

RUN wget -O ssd.tgz https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1?tf-hub-format=compressed && \
    mkdir -p /tmp/myapp/models/thing/ssd && \
    tar -xzf ssd.tgz -C /tmp/myapp/models/thing/ssd && \
    rm ssd.tgz 

RUN apt update && apt -y install cmake ffmpeg exiftool

ADD https://github.com/rcmalli/keras-vggface/releases/download/v2.0/rcmalli_vggface_tf_notop_resnet50.h5 /root/.keras/models/vggface/

#ADD https://github.com/serengil/deepface_models/releases/download/v1.0/gender_model_weights.h5 /tmp/myapp/models/facial/
#ADD https://github.com/serengil/deepface_models/releases/download/v1.0/age_model_weights.h5 /tmp/myapp/models/facial/
ADD https://github.com/serengil/deepface_models/releases/download/v1.0/facial_expression_model_weights.h5 /tmp/myapp/models/facial/

# COPY models/face/rcmalli_vggface_tf_notop_resnet50.h5 /root/.keras/models/vggface/
COPY requirements.txt /tmp
# RUN cd /tmp && pipenv lock --requirements > requirements.txt
RUN cd /tmp && pip install -r requirements.txt
COPY . /tmp/myapp
RUN pip install /tmp/myapp

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.3/wait /tmp/myapp/wait
RUN chmod +x /tmp/myapp/wait
#RUN groupadd -g 999 celery && \
#    useradd -r -u 999 -g celery celery
#USER celery

EXPOSE 5000
WORKDIR /tmp/myapp
COPY envs/env.docker .env

# CMD ["/usr/bin/supervisord"]
ENTRYPOINT ["/tmp/myapp/docker-entrypoint.sh"]
# ENTRYPOINT ["tail", "-f", "/dev/null"]