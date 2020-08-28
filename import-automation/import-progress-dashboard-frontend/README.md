# Import Progress Dashboard Frontend

This directory contains code for the frontend for the Import Progress Dashboard.
The frontend has two components: a server and a client. The client is a single
page application that displays a table of system runs and the server serves the
web page and retrieves data from the Import Progress Dashboard API for the
client.

## Deploying to App Engine

```
cd client
npm install
npm run-script build
cd ..
gcloud app deploy
```
