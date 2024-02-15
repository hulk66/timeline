#!/bin/bash
set -o allexport; source .env; set +o allexport
sudo ln -s ${ASSET_PATH} /photos
sudo ln -s ${PREVIEW_PATH}:/preview
