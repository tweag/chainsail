import 'tailwindcss/tailwind.css';
import 'katex/dist/katex.min.css';
import '../style/global.css';

import { AuthProvider } from '../components/Auth';
import useWindowDimensions from '../utils/windowDimensions';
import { sm } from '../utils/breakPoints';
import { useEffect } from 'react';

import LogRocket from 'logrocket';
import setupLogRocketReact from 'logrocket-react';

function MyApp({ Component, pageProps }) {
  useEffect(() => {
    try {
      // only initialize when in the browser
      if (window !== undefined) {
        LogRocket.init('9snsmi/chainsail');
        setupLogRocketReact(LogRocket);
      }
    } catch (e) {
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
