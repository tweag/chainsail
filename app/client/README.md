# client

The `client` is based on [Next.js](https://nextjs.org/) framework and bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).
We use [Tailwindcss](https://tailwindcss.com/) for CSS styling.

### Develop

First use `nix-shell` from the project root directory.
It helps all developers to have an identical environment with the required build inputs.
Then come back to the `client` directory, install the dependencies and run the development server:

```bash
cd client && yarn install && yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

[API routes](https://nextjs.org/docs/api-routes/introduction) can be accessed on [http://localhost:3000/api/hello](http://localhost:3000/api/hello). This endpoint can be edited in `pages/api/hello.js`.

The `pages/api` directory is mapped to `/api/*`. Files in this directory are treated as [API routes](https://nextjs.org/docs/api-routes/introduction) instead of React pages.

### Firebase

Make sure to copy your [firebase](https://firebase.google.com/) credentials to the project directory
for the login to work properly. Firebase admin configuration information should be placed in
`firebase-admin-secrets.json` and client configuration in `.env.local`.
The desired interface for `.env.local` is given in `.env.local.example`.

### Deployment

## ... with Docker

Create a `.env.local` file in the client directory and feed it with the appropriate environment variables
(see `.env.local.example` for the interface). Then use the `Dockerfile` provided in the client
directory to build an image:

```shell
$ docker build -t resaas-client:latest .
```

To run the docker image make sure to fill `next.config.js` file with firebase secrets and mirror it
to the appropriate path as follows:

```shell
$ docker run -v $PWD/next.config.js:/opt/app/next.config.js\
  -p 3000:3000\
  -e GRAPHITE_URL=<GRAPHITE_URL> \
  -e SCHEDULER_URL=<SCHEDULER_URL> \
  resaas-client:latest
```

## ... to AppEngine

Run

```shell
$ npm run deploy
```
