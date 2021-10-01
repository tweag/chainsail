import 'tailwindcss/tailwind.css';
import 'katex/dist/katex.min.css';
import '../style/global.css';

import { AuthProvider } from '../components/Auth';
import useWindowDimensions from '../utils/windowDimensions';
import { sm } from '../utils/breakPoints';
import { useEffect } from 'react';

function MyApp({ Component, pageProps }) {
  useEffect(()=> {
    try {
      // you can import these packages anywhere
      const LogRocket = require('logrocket');
      const setupLogRocketReact = require('logrocket-react');
      
      // only initialize when in the browser
      if (window !== undefined) {
        LogRocket.init('9snsmi/chainsail');
        setupLogRocketReact(LogRocket);
        
        const {uid, email} = pageProps;
        if(uid !== undefined && email !== undefined) {
          LogRocket.identify(uid, {
            email: email,
          });
        }
      }
    } catch(e) {
      console.log(e);
    }
  }, []);
  // To check if the screen is for mobile
  const { width } = useWindowDimensions();
  const isMobile = width <= sm;

  return (
    <AuthProvider>
      <Component {...pageProps} isMobile={isMobile} />
    </AuthProvider>
  );
}

export default MyApp;
