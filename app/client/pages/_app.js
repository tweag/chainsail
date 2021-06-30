import 'tailwindcss/tailwind.css';
import 'katex/dist/katex.min.css';
import '../style/global.css';

import { AuthProvider } from '../components/Auth';
import useWindowDimensions from '../utils/windowDimensions';
import { sm } from '../utils/breakPoints';

function MyApp({ Component, pageProps }) {
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
