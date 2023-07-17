PHONY: install build push


install:
	pip install -r requirements.txt
	mkdir -p tmp
	wget -O tmp/ssd.tgz https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1?tf-hub-format=compressed && \
    mkdir -p tmp/ssd && \
    tar -xzf tmp/ssd.tgz -C tmp/ssd && \
    rm ssd.tgz 

build:
	docker build . -t hulk66/timeline_be:0.96

push:	
	docker push hulk66/timeline_be:0.96
