# client

The `client` is based on [Next.js](https://nextjs.org/) framework and bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).
We use [Tailwindcss](https://tailwindcss.com/) for CSS styling.

### Firebase

Make sure to copy your [firebase](https://firebase.google.com/) credentials to the project directory
for the login to work properly. Client configuration should be placed in `.env.local`.
The desired interface for `.env.local` is given in `.env.local.example`.

### Develop

Get a key for the `resaas-client@resaas-simeon-dev.iam.gserviceaccount.com` service account, which has the correct permissions to access the Firebase admin secrets in Google Cloud Secret Manager.
Save that key to, say, `client_sa_key.json`.
Then use `nix-shell` from the project root directory.
It helps all developers to have an identical environment with the required build inputs.
Then come back to the `client` directory, install the dependencies and run the development server:

```bash
$ cd client
$ yarn # install the dependencies
$ GOOGLE_APPLICATION_CREDENTIALS=client_sa_key.json yarn dev # run a dev server
```

To get the local client connect to the cloud backend, first set the GCP ssh keys :

```
$ gcloud config set project resaas-simeon-dev
$ gcloud compute config-ssh
```

And then open an ssh channel to the Google Cloud VM like so:

```
$ ssh -L 8080:localhost:8080 -L 5000:localhost:5000 -L 8081:localhost:8081 resaas-dev.europe-west3-c.resaas-simeon-dev
```

That opens a new shell, which you don't use. Then open a new shell (on your local machine) and run the client locally with

```
$ GOOGLE_APPLICATION_CREDENTIALS=client_sa_key.json \
  GRAPHITE_URL=http://localhost:8080 \
  SCHEDULER_URL=http://localhost:5000 \
  MCMC_STATS_URL=http://localhost:8081 \
  yarn run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

[API routes](https://nextjs.org/docs/api-routes/introduction) can be accessed on [http://localhost:3000/api/hello](http://localhost:3000/api/hello). This endpoint can be edited in `pages/api/hello.js`.

The `pages/api` directory is mapped to `/api/*`. Files in this directory are treated as [API routes](https://nextjs.org/docs/api-routes/introduction) instead of React pages.

### Deployment

## ... with Docker

Create a `.env.local` file in the client directory and feed it with the appropriate environment variables
(see `.env.local.example` for the interface). Then use the `Dockerfile` provided in the client
directory to build an image:

```shell
$ docker build -t chainsail-client:latest .
```

To run the docker image:

```shell
$ docker run \
    -v /path/to/client_service_account_key.json:/config/client_sa_key.json \
	-e GOOGLE_APPLICATION_CREDENTIALS=/config/client_sa_key.json \
    -p 3000:3000\
    -e GRAPHITE_URL=<GRAPHITE URL> \
    -e SCHEDULER_URL=<SCHEDULER URL> \
	-e MCMC_STATS_URL=<MCMC STATS SERVER URL> \
    chainsail-client:latest
```

## ... to AppEngine

Create a file `app.yaml` file from the template in `app.yaml.template`. To make completing the required fields easier, here's some useful information:

By default, on our current dev VMs, the ports are

- 8000 for Graphite,
- 80 for the scheduler,
- 8081 for the MCMC stats server.

The two current development VMs have the following IPs:

- `resaas-dev`: 10.156.0.2
- `ressas-dev2`: 10.156.0.3

The project number can be obtained via the following command:

```bash
$ gcloud projects list --format="value(PROJECT_NUMBER)"
```

The location is currently "europe-west3" and the connector ID can be obtained via

```bash
$ gcloud compute networks vpc-access connectors list --region europe-west3 --format="value(CONNECTOR_ID)"
```

If you'd like to deploy a new / different service (meaning, not the default one which `chainsail.io` points to), change `service: default` to, e.g., `service: test`.
Once all fields are filled in, run:

```shell
$ npm run deploy
```
