# About Overturemaps-WFSServer
This repository contains a Proof of Concept about providing an interface for accessing Overturemaps layers -directly from geoparquet files in S3- by a OGC WFS service.

# Project setup
Note: instructions for a Linux environment (tested with Ubuntu)

## Step 1 - Checkout project
git clone https://github.com/jemacchi/overturemaps-wfsserver.git

## Step 2 - Start docker compose
docker compose up -d

## Step 3 - Test app
Now you can access Django admin panel at http://localhost:8000/admin
Also you can access Geoserver at http://localhost:8080/geoserver/web  (admin/geoserver) and check the layer named "new-york"

You can create a superuser accessing the overturemapsserver container and executing following command
python manage.py createsuperuser

# How To

## Install dependencies
apt-get update
apt-get install binutils libproj-dev gdal-bin libgdal-dev build-essential libssl-dev libffi-dev python3-dev python3.10-venv

## Create and activate virtualenv
cd overturemaps-wfsserver
python3 -m venv overturemaps_wfsserver_env
source overturemaps_wfsserver_env/bin/activate  

## Install django and dependencies
cd overturemaps_wfsserver
pip install -r requirements.txt

## Set workarounds
cd ..
cp overturemaps_wfsserver/workarounds/wfs20.py ./overturemaps_wfsserver_env/lib/python3.10/site-packages/gisserver/operations/

## Database schema update
Whenever you modify Django models code in the app, then probably you will need to execute these 2 commands (or to restart the docker container named overturemapsserver, depending on how you run the overturemaps server)

python manage.py makemigrations
python manage.py migrate

# Documentation & related links

- FOSS4G 2024 - Belem, Brazil
  
  Resume: https://talks.osgeo.org/foss4g-2024/talk/FW8L77/
  
  Slides: https://talks.osgeo.org/media/foss4g-2024/submissions/FW8L77/resources/foss4g_2024_overturemaps_ZgEpoRc.pdf
