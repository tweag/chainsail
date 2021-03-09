import getConfig from 'next/config';
import admin from 'firebase-admin';

const { serverRuntimeConfig } = getConfig();
const serviceAccount = serverRuntimeConfig.firebaseAdminSecrets;

export const verifyIdToken = (token) => {
  if (!admin.apps.length) {
    admin.initializeApp({
      credential: admin.credential.cert(serviceAccount),
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
