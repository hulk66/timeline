PHONY: install build push

install:
	npm i

build:
	docker build . -t hulk66/timeline_fe:${IMAGE_VERSION}

push:	
	docker push hulk66/timeline_fe:${IMAGE_VERSION}

dev:
	npm run serve
