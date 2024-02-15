PHONY: install build push


install:
	cd backend && make install
	cd frontend && make install

backup:
	scripts/backup-db.sh

clean: 
	read -p "Warning - it will remove all the previews, database and logs. ARE YOU SURE? " -n 1 -r
	echo    # (optional) move to a new line
	if [[ $REPLY =~ ^[Yy]$ ]]
	then
		docker-compose down -v
		sudo rm -rf data/db/* data/preview/* data/rabbitmq/* data/log/*
	fi

build:
	cd backend && make build
	cd frontend && make build

rebuild:
	docker compose down worker frontend transcoder watchdog webapp
	cd backend && make build
	cd frontend && make build
	docker compose up -d

push:	
	cd backend && make push
	cd frontend && make push

run-dev-support:
	docker compose up -d redis db adminer rabbitmq

run-dev-worker:
	docker compose up -d worker

down:
	docker compose down

up:
	docker compose up -d

up-storage:
	docker compose up -d redis db adminer rabbitmq

download-model:
	# this is only required if you want to develop locally and only once in the beginning
	wget -O backend/ssd.tgz "https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1?tf-hub-format=compressed"

	mkdir backend/models/facial

	wget https://github.com/serengil/deepface_models/releases/download/v1.0/gender_model_weights.h5
	mv gender_model_weights.h5 backend/models/facial/

	wget https://github.com/serengil/deepface_models/releases/download/v1.0/age_model_weights.h5
	mv age_model_weights.h5 backend/models/facial/

	wget https://github.com/serengil/deepface_models/releases/download/v1.0/facial_expression_model_weights.h5
	mv facial_expression_model_weights.h5 backend/models/facial/

make-dev-dirs:
	scripts/setup-dev-dirs.sh