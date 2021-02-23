import 'tailwindcss/tailwind.css';
import 'katex/dist/katex.min.css';
import '../style/global.css';

import { AuthProvider } from '../components/Auth';

function MyApp({ Component, pageProps }) {
  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  );
}

export default MyApp;
