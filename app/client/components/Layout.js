import Head from 'next/head';
import Container from './Container';
import { FlexCol } from './Flex';
import Navbar from './Navbar';

export default function Layout({ children }) {
  return (
    <>
      <Head>
        <title>Resaas</title>
        <link rel="preconnect" href="https://fonts.gstatic.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP&display=swap"
          rel="stylesheet"
        />
        <link
          rel="stylesheet"
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css"
          integrity="sha512-+4zCK9k+qNFUR5X+cKL9EIR+ZOhtIloNl9GIKS57V1MyNsYpYcUrUeQc9vNfzsWfV28IaLL3i96P9sdNyeRssA=="
          crossOrigin="anonymous"
        />
      </Head>
      <Container className="text-white bg-gradient-to-r from-purple-900 to-indigo-600 lg:h-screen font-body">
        <FlexCol between className="h-full">
          <Navbar />
          {children}
        </FlexCol>
      </Container>
    </>
  );
}
