# GCP Test

This project shows how to integrate github workflows with Google Cloud Platform. The aim is to deploy the application everytime there is a push to the main branch. It uses a service account.

## Clone and Build the Project
Clone the project. Create a python virtual environment. Install Flask and run
```
git clone https://github.com/davidzof/gcptest.git
python3 -m venv venv
source venv/bin/activate
pip install flask
python app.py
```
The app should be available on port 8080, the port is set in the code

## Docker
Create a requirements.txt file. You probably just need to keep flask without and version number. Build and tag the docker image. Run the image.

```
pip freeze > requirements.txt 
docker build --tag hello-world .
docker image ls
docker run hello-world
```

Note a requirements.txt is included in the github repo

## Google Cloud Platform

Create a project from the Google Cloud console. You can create a free 3 month trial GCP account if you don't have one.

You will either need to use the GCP console or install the Google Cloud SDK. Once you are logged in set the active project

$ gcloud config set project <PROJECT_ID> 

Replace <PROJECT_ID> with your GCP project ID.

### Enable Required APIs

$ gcloud services enable containerregistry.googleapis.com

### Create a Google Cloud Storage Bucket for Container Registry

$ gcloud artifacts repositories create <REPO_NAME> \
  --repository-format=docker \
  --location=<REGION> \
  --description="Docker repository for images"

Replace <REPO_NAME> with your choice of name
Replace <REGION> with the region where you want to create the repo e.g. europe-west9 (Paris)

### Create a service account

$ gcloud iam service-accounts create github-actions \
  --description="Service account for GitHub Actions" \
  --display-name="GitHub Actions Service Account"

and assign the necessary roles

$ gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:github-actions@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

Replace <PROJECT_ID> with your GCP project ID.

### Create a JSON Key for the Service Account
  
$ gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@<PROJECT_ID>.iam.gserviceaccount.com

Replace <PROJECT_ID> with your GCP project ID. Save this key somewhere.

### Add the Key to GitHub Secrets

1. Open your GitHub repository in a browser.
2. Go to Settings > Secrets and variables > Actions > New repository secret.
3. Create a new secret named GCP_SERVICE_ACCOUNT_KEY and paste the contents of key.json.

Note this is considered less secure than using Workload Identity Federations where no key is stored on the github side.

https://github.com/google-github-actions/auth#preferred-direct-workload-identity-federation

# Set Up GitHub Workflow

see: https://github.com/davidzof/gcptest/blob/main/.github/workflows/google-cloudrun-docker.yml

Basically this

1. authenticates with Google Cloud using the GCP_SERVICE_ACCOUNT_KEY above
2. installs the Google SDK on Github
3. authenticates with docker
4. builds and tags a docker image
5. pushes the tagged image to the GCP repo we created above
6. installs the image as a public accessible service

The last point requires extra permissions on the Google Service Account we created

```bash
$ gcloud projects add-iam-policy-binding github-test-project-442816 \
  --member="serviceAccount:github-actions@github-test-project-442816.iam.gserviceaccount.com" \
  --role="roles/run.admin"

$ gcloud projects add-iam-policy-binding github-test-project-442816 \
  --member="serviceAccount:github-actions@github-test-project-442816.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

$ gcloud projects add-iam-policy-binding github-test-project-442816 \
  --member="serviceAccount:github-actions@github-test-project-442816.iam.gserviceaccount.com" \
  --role="roles/run.viewer"

$ gcloud iam service-accounts add-iam-policy-binding 776737377276-compute@developer.gserviceaccount.com \
  --member="serviceAccount:github-actions@github-test-project-442816.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

This adds a lot of extra roles to the service account, which makes it less secure. You could create the service in the Google console using a specific image tag <VERSION> or latest. Whenever the docker image is pushed it should get redeployed. You don't need to create the service in the github workflow.

## Debugging

### Verify that the repo exists

$ gcloud artifacts repositories list --location=<REGION>

Replace REGION with the region

### Test the docker bulid process locally

```bash
$ gcloud auth activate-service-account --key-file=key.json
$ gcloud auth configure-docker europe-west9-docker.pkg.dev

$ docker build -t europe-west9-docker.pkg.dev/github-test-project-442816/myrepo/my-app:latest .
$docker push europe-west9-docker.pkg.dev/github-test-project-442816/myrepo/my-app:latest
```


