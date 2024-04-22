PHONY: install build push


install:
	pip install -r requirements.txt
	wget -O ssd.tgz https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1?tf-hub-format=compressed

build:
	docker build . -t hulk66/timeline_be:${IMAGE_VERSION}

build-base:
	docker build . -f Dockerfile.be-base -t hulk66/timeline_be_base:${IMAGE_VERSION}

push:	
	docker push hulk66/timeline_be:${IMAGE_VERSION}
