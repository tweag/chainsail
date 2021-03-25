import { useState, useEffect } from 'react';
import nookies from 'nookies';
import StyledFirebaseAuth from 'react-firebaseui/StyledFirebaseAuth';
import firebase from 'firebase/app';
import 'firebase/auth';

import { FlexCenter, FlexCol, Layout } from '../components';

import firebaseClient from '../utils/firebaseClient';

const FirebaseAuth = ({ latestPage }) => {
  firebaseClient();
  const [renderAuth, setRenderAuth] = useState(false);
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setRenderAuth(true);
    }
  }, []);
  const firebaseAuthConfig = {
    signInFlow: 'popup',
    // Auth providers
    // https://github.com/firebase/firebaseui-web#configure-oauth-providers
    signInOptions: [firebase.auth.GoogleAuthProvider.PROVIDER_ID],
    signInSuccessUrl: latestPage,
    credentialHelper: 'none',
  };
  return (
    <Layout>
      <div className="h-screen text-white bg-gradient-to-r from-purple-900 to-indigo-600 font-body">
        {renderAuth ? (
          <FlexCenter className="w-full h-full pb-72">
            <FlexCol between className="px-10 pt-12 pb-5 bg-indigo-500 shadow-lg w-96 rounded-xl">
              <div className="text-lg mb-5">Please login using your Google account *</div>
              <div className="mb-8 text-xs">
                * No personal data is gathered. This is only to link your jobs to your identity and
                to calculate your compute time quota.
              </div>
              <StyledFirebaseAuth uiConfig={firebaseAuthConfig} firebaseAuth={firebase.auth()} />
            </FlexCol>
          </FlexCenter>
        ) : null}
      </div>
    </Layout>
  );
};

export async function getServerSideProps(ctx) {
  // Parse
  const cookies = nookies.get(ctx);
  return { props: { latestPage: cookies.latestPage || '/' } };
}

export default FirebaseAuth;
