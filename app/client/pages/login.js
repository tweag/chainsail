import { useState, useEffect } from 'react';
import StyledFirebaseAuth from 'react-firebaseui/StyledFirebaseAuth';
import firebase from 'firebase/app';
import 'firebase/auth';

import { FlexCenter, Layout } from '../components';

import firebaseClient from '../utils/firebaseClient';

const firebaseAuthConfig = {
  signInFlow: 'popup',
  // Auth providers
  // https://github.com/firebase/firebaseui-web#configure-oauth-providers
  signInOptions: [firebase.auth.GoogleAuthProvider.PROVIDER_ID],
  signInSuccessUrl: '/',
  credentialHelper: 'none',
};

const FirebaseAuth = () => {
  firebaseClient();
  const [renderAuth, setRenderAuth] = useState(false);
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setRenderAuth(true);
    }
  }, []);
  return (
    <Layout>
      {renderAuth ? (
        <FlexCenter className="w-full mt-20">
          <div className="px-5 py-8 bg-indigo-500 shadow-lg w-96 rounded-xl">
            <FlexCenter className="mb-5 w-full">Please login using your Google account</FlexCenter>
            <StyledFirebaseAuth uiConfig={firebaseAuthConfig} firebaseAuth={firebase.auth()} />
          </div>
        </FlexCenter>
      ) : null}
    </Layout>
  );
};

export default FirebaseAuth;
