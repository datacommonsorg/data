Deploy to GKE

Import-automation executor can also be deployed to gke. After committing new changes, please do the following to deploy.

1. From repo root, run: `cd import-automation/executor`

2. build and push image: `./gke/push_image.sh`

3. Replace image tag in deployment.yaml with the value of `git rev-parse --short=7 HEAD`.

4. Update GKE with the following.

```sh
gcloud container clusters get-credentials datacommons-us-central1 \
  --region us-central1 --project datcom-website-dev

kubectl apply -f gke/deployment.yaml
```
