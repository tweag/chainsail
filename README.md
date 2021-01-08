# RESAAS: Replica Exchange sampling as-a-service

A first draft of how this service looks like can be found [here](https://docs.google.com/document/d/1DcTozCzTmUbJbhQtj-tYSYvWHRpI2I_mOWS19BOutlk/edit?ts=5ff44579).

## Client

The front-end part it located in `client` directory. It is written on [Next.js](https://nextjs.org/) framework and bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app). We use [Tailwindcss](https://tailwindcss.com/) for CSS styling.

### Develop

First use `nix-shell` to enter to a proper environment with the required build inputs. Then move to `client` directory, install the dependencies and run the development server:

```bash
cd client && yarn install && yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

[API routes](https://nextjs.org/docs/api-routes/introduction) can be accessed on [http://localhost:3000/api/hello](http://localhost:3000/api/hello). This endpoint can be edited in `pages/api/hello.js`.

The `pages/api` directory is mapped to `/api/*`. Files in this directory are treated as [API routes](https://nextjs.org/docs/api-routes/introduction) instead of React pages.

### Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

### Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/import?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more details.
