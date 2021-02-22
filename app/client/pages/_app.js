import 'tailwindcss/tailwind.css';
import 'katex/dist/katex.min.css';
import '../style/global.css';
import initAuth from '../utils/initAuth';

initAuth();

function MyApp({ Component, pageProps }) {
  return <Component {...pageProps} />;
}

export default MyApp;
