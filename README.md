# GCP Test
David George, December 2024

This project shows how to integrate github workflows with Google Cloud Platform (GCP).
The objective was to deploy the application whenever there is a push/merge to the main branch.

## Using a service Account

This is relatively simple to get working but is not considered best practise as a secret has
to be stored on the client side. If this can be accessed somehow it could be used to gain at
least partial access to the GCP project.

### Step 1: Clone and Build the Project

This tutorial uses a very simple python project. It could just as easily be a Spring
boot application. The aim is to build, package, push and deploy a Web application.

Clone the project. Create a python virtual environment. Install Flask and run

```
git clone https://github.com/davidzof/gcptest.git
python3 -m venv venv
source venv/bin/activate
pip install flask
python app.py
```

The app should be available on port 8080, the port is set in the code

### Docker Container
Create a requirements.txt file. You probably just need to keep flask without and version number. Build and tag the docker image. Run the image.

```
pip freeze > requirements.txt 
docker build --tag hello-world .
docker image ls
docker run hello-world
```

Note a requirements.txt is included in this github repo

### Deploy to Google Cloud Platform

Create a project from the Google Cloud console. You can create a free 3 month trial GCP account if you don't have one.

You will either need to use the GCP console or install the Google Cloud SDK.
This video shows you how to do this: https://youtu.be/-oyePtbnrgs?feature=shared&t=1370

Once you are logged in to GCP set the active project

$ gcloud config set project <PROJECT_ID> 

Replace <PROJECT_ID> with your GCP project ID.

### Enable Required APIs

$ gcloud services enable containerregistry.googleapis.com

#### Create a Google Cloud Storage Bucket for Container Registry

$ gcloud artifacts repositories create <REPO_NAME> \
  --repository-format=docker \
  --location=<REGION> \
  --description="Docker repository for images"

Replace <REPO_NAME> with your choice of name
Replace <REGION> with the region where you want to create the repo e.g. europe-west9 (Paris)

#### Create a service account

replace <SERVICE_ACCOUNT_NAME> with your name, i.e "github-actions"

$ gcloud iam service-accounts create <SERVICE_ACCOUNT_NAME> \
  --description="Service account for GitHub Actions" \
  --display-name="GitHub Actions Service Account"

and assign the necessary roles

$ gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:<SERVICE_ACCOUNT_NAME>@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

Replace <PROJECT_ID> with your GCP project ID.

#### Create a JSON Key for the Service Account
  
$ gcloud iam service-accounts keys create key.json \
  --iam-account=<SERVICE_ACCOUNT_NAME>@<PROJECT_ID>.iam.gserviceaccount.com

Replace <PROJECT_ID> with your GCP project ID. Save this key somewhere.

#### Add the Key to GitHub Secrets

1. Open your GitHub repository in a browser.
2. Go to Settings > Secrets and variables > Actions > New repository secret.
3. Create a new secret named GCP_SERVICE_ACCOUNT_KEY and paste the contents of key.json.

Note this is considered less secure than using Workload Identity Federations where no
key is stored on the github side.

https://github.com/google-github-actions/auth#preferred-direct-workload-identity-federation

### Set Up GitHub Workflow

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
  --member="serviceAccount:<SERVICE_ACCOUNT_NAME>@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/run.admin"

$ gcloud projects add-iam-policy-binding github-test-project-442816 \
  --member="serviceAccount:<SERVICE_ACCOUNT_NAME>@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

$ gcloud projects add-iam-policy-binding github-test-project-442816 \
  --member="serviceAccount:<SERVICE_ACCOUNT_NAME>@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/run.viewer"

$ gcloud iam service-accounts add-iam-policy-binding 776737377276-compute@developer.gserviceaccount.com \
  --member="serviceAccount:<SERVICE_ACCOUNT_NAME>@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

This adds a lot of extra roles to the service account, which makes it less secure.
You could create the service in the Google console using a specific image tag <VERSION> or latest. Whenever the docker image is pushed it should get redeployed. You don't need to create the service in the github workflow.

## Debugging

### Verify that the repo exists

$ gcloud artifacts repositories list --location=<REGION>

Replace REGION with the region

### Test the docker build and deploy process from the console

```bash
$ gcloud auth activate-service-account --key-file=key.json
$ gcloud auth configure-docker <REGION>-docker.pkg.dev

$ docker build -t <REGION>-docker.pkg.dev/<PROJECT_ID>/<REPO_NAME>/my-app:latest .
$ docker push <REGION>-docker.pkg.dev/<PROJECT_ID>/<REPO_NAME>/my-app:latest
```

## Authenticating with Workflow Identity Federation (WIF)

This is more secure as there is no shared secret key but is a lot more touchy to setup because
a lot of the documentation on the web is out-of=date. This information was correct as of
December 2024. I can only suggest carefully reading the latest version of these documents.

### Creating a service account

```bash
gcloud iam service-accounts create <SERVICE_ACCOUNT_NAME> \
    --description="Service account for GitHub Actions with WIF" \
    --display-name="<DISPLAY_NAME>"
```

* Replace <SERVICE_ACCOUNT_NAME> with a unique name (e.g., github-actions-sa).
* Replace <DISPLAY_NAME> with a descriptive name (e.g., GitHub Actions Service Account).

### Grant the Service Account Necessary Roles

1. Push to Artifact Registry: roles/artifactregistry.writer
1. Deploy to Cloud Run: roles/run.admin
1. View logs in Cloud Logging: roles/logging.viewer
1. Pull secret from Secret Manager: roles/secretmanager.secretAccessor

Use this command

```bash
gcloud projects add-iam-policy-binding <PROJECT_ID> \
    --member="serviceAccount:<SERVICE_ACCOUNT_NAME>@<PROJECT_ID>.iam.gserviceaccount.com" \
    --role="<ROLE>"
```

### Create a Workload IdentityFederation

A Workload Identity Federation is a feature that allows non-Google Cloud workloads (such as applications running outside of GCP) to access GCP resources securely without requiring a Google Cloud Service Account key. Instead, it uses OpenID Connect (OIDC) or similar token-based authentication mechanisms to establish a secure identity relationship between the external workload and GCP.

Key Concepts: 
1. The external application is mapped to a GCP service account which we created above
1. GCP integrates with external identity providers (IdPs) like GitHub, AWS IAM or any other OIDC-compliant system.
1. The external workload provides a token issued by its identity provider, which GCP verifies and exchanges for short-lived, GCP-specific access tokens. These tokens grant access to GCP resources.

#### Create a workload Identity Pool

```bash
gcloud iam workload-identity-pools create <POOL_NAME> \ --project=<PROJECT_ID> \
    --location="global" \ --display-name="GitHub Actions Pool"
```

### Debugging
talk about gcp logs

https://github.com/docker/login-action

https://github.com/marketplace/actions/docker-login

https://github.com/google-github-actions/auth?tab=readme-ov-file#indirect-wif

https://console.cloud.google.com/apis/api/iamcredentials.googleapis.com/metrics?project=myproject-443614