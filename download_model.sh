#!/bin/sh
# this is only required if you want to develop locally and only once in the beginning
wget -O ssd.tgz "https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1?tf-hub-format=compressed"
mkdir -p models/thing/ssd
tar -xzf ssd.tgz -C models/thing/ssd
rm ssd.tgz

wget https://github.com/serengil/deepface_models/releases/download/v1.0/gender_model_weights.h5
mv gender_model_weights.h5 models/facial

wget https://github.com/serengil/deepface_models/releases/download/v1.0/age_model_weights.h5
mv age_model_weights.h5 models/facial

wget https://github.com/serengil/deepface_models/releases/download/v1.0/facial_expression_model_weights.h5
mv facial_expression_model_weights.h5 models/facial