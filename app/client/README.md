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
$ ssh -L 8080:localhost:8080 -L 5000:localhost:5000 resaas-dev.europe-west3-c.resaas-simeon-dev
```

That opens a new shell, which you don't use. Then open a new shell (on your local machine) and run the client locally with

```
GOOGLE_APPLICATION_CREDENTIALS=client_sa_key.json GRAPHITE_URL=http://localhost:8080 SCHEDULER_URL=http://localhost:5000 yarn run dev
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

To run the docker image make sure to fill `next.config.js` file with firebase secrets and mirror it
to the appropriate path as follows:

```shell
$ docker run -v $PWD/next.config.js:/opt/app/next.config.js\
  -p 3000:3000\
  -e GRAPHITE_URL=<GRAPHITE_URL> \
  -e SCHEDULER_URL=<SCHEDULER_URL> \
  chainsail-client:latest
```

## ... to AppEngine

Run

```shell
$ npm run deploy
```
