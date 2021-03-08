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

Use docker to create an image and feed it with the appropriate environment variables:

```shell
$ docker build -t resaas-client3:latest \
  -e FLASK_URL=<FLASK_URL> \
  -e NEXT_PUBLIC_FIREBASE_PUBLIC_API_KEY=<FIREBASE_PUBLIC_API_KEY> \
  -e NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=<FIREBASE_AUTH_DOMAIN> \
  -e NEXT_PUBLIC_FIREBASE_PROJECT_ID=<FIREBASE_PROJECT_ID> \
  -e NEXT_PUBLIC_FIREBASE_DATABASE_URL=<FIREBASE_DATABASE_URL> \
  -e NEXT_PUBLIC_FIREBASE_MSG_SENDER_ID=<FIREBASE_MSG_SENDER_ID> \
  -e NEXT_PUBLIC_FIREBASE_APP_ID=<FIREBASE_APP_ID> \
  .
```
