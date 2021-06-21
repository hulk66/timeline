#!/bin/sh
docker-compose down -v
sudo rm -rf data/db/* data/preview/* data/rabbitmq/* data/log/*
