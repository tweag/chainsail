import { useState, useEffect, useContext, createContext } from 'react';
import nookies from 'nookies';
import firebaseClient from '../utils/firebaseClient';
import firebase from 'firebase/app';
import 'firebase/auth';
import LogRocket from 'logrocket';

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  firebaseClient();
  const [user, setUser] = useState(null);

  useEffect(() => {
    return firebase.auth().onIdTokenChanged(async (user) => {
      if (!user) {
        setUser(null);
        nookies.set(undefined, 'token', '', {});
        return;
      } else {
        try {
          LogRocket.identify(user.uid, {
            email: user.email,
            name: user.displayName,
          });
          console.log('Identified to LogRocket as ' + user.email);
        } catch (e) {
          console.log(
            'Identify failed on ' + JSON.stringify(user) + ', session will be anonymous'
          );
          console.log(e);
        }
      }

      const token = await user.getIdToken();
      setUser(user);
      nookies.set(undefined, 'token', token, {});
    });
  }, []);
  return <AuthContext.Provider value={{ user }}>{children}</AuthContext.Provider>;
};
export const useAuth = () => useContext(AuthContext);
