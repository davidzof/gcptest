# gcptest
Google Cloud Integration Test

## Build
Clone the project. Create a python virtual environment. Install Flask and run
```
git clone https://github.com/davidzof/gcptest.git
python3 -m venv venv
source venv/bin/activate
pip install flask
python app.py
```
The app should be available on port 8000

## Docker
Create a requirements.txt file. You probably just need to keep flask without and version number. Build and tag the docker image. Run the image.

```
pip freeze > requirements.txt 
docker build --tag hello-world .
docker image ls
docker run hello-world
```

## GCP

Enable 'Cloud Build API'. 

https://cloud.google.com/build/docs/automating-builds/github/connect-repo-github

gcloud config set project PROJECT_ID

Enable secret manager

https://console.cloud.google.com/apis/library/secretmanager.googleapis.com?project=bionic-unity-436718-q0

gcloud builds connections create github gcptest --region=europe-north1

