# gcptest
Google Cloud Integration Test

## Build
git clone https://github.com/davidzof/gcptest.git
python3 -m venv venv
source venv/bin/activate
pip install flask
python app.py

## Docker
pip freeze > requirements.txt 
docker build --tag hello-world .
docker image ls
docker run hello-world
