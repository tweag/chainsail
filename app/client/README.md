# Chainsail web client

The `client` is based on [Next.js](https://nextjs.org/) framework and bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).
We use [Tailwindcss](https://tailwindcss.com/) for CSS styling.

## Develop

To get all necessary non-JavaScript dependencies, best use the repository root Nix shell.
It helps all developers to have an identical environment with the required build inputs.
Then come back to the `client` directory, install the JavaScript dependencies and run the development server:

```bash
$ cd client
$ yarn # install the dependencies
$ GRAPHITE_URL=<URL to Graphite logging server> \
  SCHEDULER_URL=<URL to scheduler> \
  MCMC_STATS_URL=<URL to MCMC stats server> \
  yarn run dev
```
If you deployed the Chainsail backend via Minikube, you can use the `run_dev_client.sh` helper script to set the URL environment variables and start the development server.
Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

The `pages/api` directory is mapped to `/api/*`. Files in this directory are treated as [API routes](https://nextjs.org/docs/api-routes/introduction) instead of React pages.

## Firebase login

### Activating / deactivating mandatory Firebase login

For development purposes and when you're sure you don't need to identify your users, you can deactivate mandatory Firebase login by setting `require_auth = false` in the `serverRuntimeConfig` section of `./next.js.config`.
This is the default.
Setting the same setting to `true` makes Firebase login mandatory and passes a user's email address and an unique user ID along to the scheduler.
Note that the scheduler has a separate authorisation check, which you can enable or disable in the scheduler settings section of the [Helm charts](../../helm) (`values-dev.yaml` for Google Cloud deployment, `values-local.yaml` for deployment using Minikube).

### Providing Firebase credentials

Make sure to copy your [Firebase](https://firebase.google.com/) credentials to the project directory for the login to work properly. Client configuration should be placed in `.env.local`.
The desired interface for `.env.local` is given in `.env.local.example`.

Firebase admin credentials are expected to be found in Google Cloud Secret Manager; the secret name can be configured in `next.config.js`.
Once that is done, get a key for a service account that has the correct permissions to access the Firebase admin secrets in Google Cloud Secret Manager.
Save that key to, say, `client_sa_key.json`.
Then set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of `client_sa_key.json` before running `yarn run dev` or another command that serves the application.


## Deployment

### ... with Docker

Create a `.env.local` file in the client directory and feed it with the appropriate environment variables
(see `.env.local.example` for the interface). Then use the `Dockerfile` provided in the client
directory to build an image:

```shell
$ docker build -t chainsail-client:latest .
```

To run the docker image:

```shell
$ docker run \
    -p 3000:3000\
    -e GRAPHITE_URL=<GRAPHITE URL> \
    -e SCHEDULER_URL=<SCHEDULER URL> \
	-e MCMC_STATS_URL=<MCMC STATS SERVER URL> \
    chainsail-client:latest
```
If using Firebase authentication, remember to mount in the service account key and set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable by adding
```console
-v /path/to/client_service_account_key.json:/config/client_sa_key.json \
-e GOOGLE_APPLICATION_CREDENTIALS=/config/client_sa_key.json \
```
to the above command.

### ... to AppEngine

If deploying the client to AppEngine and the backend via Terraform and Helm on Google Cloud, make sure to also create a [VPC connector](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access) that allows the App Engine deployment to access the VPC the backend works in.

Once that is done, create a file `app.yaml` file from the template in `app.yaml.template`.

The project number for the VPC connector setting can be obtained via the following command:
```bash
$ gcloud projects list --format="value(PROJECT_NUMBER)"
```
The connector ID can be obtained via

```bash
$ gcloud compute networks vpc-access connectors list --region <connector region> --format="value(CONNECTOR_ID)"
```

If you'd like to deploy a new / different service, change `service: default` to, e.g., `service: test`.
Once all fields are filled in, run:

```shell
$ npm run deploy
```
