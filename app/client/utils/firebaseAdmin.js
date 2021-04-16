import getConfig from 'next/config';
import admin from 'firebase-admin';

const { serverRuntimeConfig } = getConfig();
// Imports the Secret Manager library
const { SecretManagerServiceClient } = require('@google-cloud/secret-manager');
// Instantiates a client
const client = new SecretManagerServiceClient();

async function accessSecretVersion() {
  const [version] = await client.accessSecretVersion({
    name: serverRuntimeConfig.secret_name,
  });
  process.stdout.write(version.payload.data + '\nOHOO\n');
  const json_obj = JSON.parse(version.payload.data.toString());
  return json_obj;
}

export const verifyIdToken = async (token) => {
  if (!admin.apps.length) {
    const accessSecret = await accessSecretVersion();
    admin.initializeApp({
      credential: admin.credential.cert(accessSecret),
      databaseURL: process.env.NEXT_PUBLIC_FIREBASE_DATABASE_URL,
    });
  }

  return admin
    .auth()
    .verifyIdToken(token)
    .catch((error) => {
      throw error;
    });
};
