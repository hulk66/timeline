PHONY: install build push


install:
	cd backend && make install
	cd frontend && make install

backup:
	docker compose down worker transcoder watchdog webapp frontend
	cd data/backups/db && \
	set -o allexport; source .env; set +o allexport && \
	NOW_DATE=$(date +"%Y-%m-%d %T") NOW_DATE_FN=$(echo $NOW_DATE |  tr '[: ]' '_') \
	mysqldump timeline --result-file="timeline-${NOW_DATE_FN}-dump.sql" --host=localhost --port 3306 --user=root$DB_SUPER_USER --password=$DB_SUPER_USER_PW
	docker compose up -d

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

push:	
	cd backend && make push
	cd frontend && make push

run-dev-support:
	docker compose up -d redis db adminer rabbitmq transcoder

run-dev-worker:
	docker compose up -d worker

down:
	docker compose down

up:
	docker compose up -d

download-model:
	# this is only required if you want to develop locally and only once in the beginning
	wget -O ssd.tgz "https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1?tf-hub-format=compressed"
	mkdir -p backend/models/thing/ssd
	tar -xzf ssd.tgz -C backend/models/thing/ssd
	#rm ssd.tgz

	mkdir backend/models/facial

	wget https://github.com/serengil/deepface_models/releases/download/v1.0/gender_model_weights.h5
	mv gender_model_weights.h5 backend/models/facial/

	wget https://github.com/serengil/deepface_models/releases/download/v1.0/age_model_weights.h5
	mv age_model_weights.h5 backend/models/facial/

	wget https://github.com/serengil/deepface_models/releases/download/v1.0/facial_expression_model_weights.h5
	mv facial_expression_model_weights.h5 backend/models/facial/
