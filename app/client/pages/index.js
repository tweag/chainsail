import { Layout, Button, FlexCenter, FlexCol, Container, Navbar } from '../components';

const Heading = () => (
  <FlexCol center className="h-full">
    <div className="mb-10 text-5xl md:text-9xl">RESAAS</div>
    <div className="mb-10 text-2xl lg:w-2/3 md:text-4xl md:mb-20">
      sampling multimodal distributions made easy
    </div>
    <div className="text-base md:text-xl lg:w-2/3 md:text-justify mb-7">
      <FlexCol className="space-y-5">
        <div>
          RESAAS helps to sample multimodal distributions by implementing an automatically scaling
          Replica Exchange MCMC algorithm. All you need to provide is a Python module defining your
          probability density and its log-probability gradient.
        </div>
        <div>
          This beta version of RESAAS is free (you have a compute time quota of 20 replicas x 2
          hours).
        </div>
        <FlexCol className="space-y-2">
          <div>To learn more about the MCMC algorithms used in RESAAS, see our blog posts:</div>
          <FlexCol>
            <a
              href="https://www.tweag.io/blog/2020-10-28-mcmc-intro-4/"
              target="_blank"
              className="transition duration-300 hover:opacity-50"
            >
              <i className="fas fa-chevron-right ml-2 mr-5"></i>
              Replica Exchange
            </a>
            <a
              href="https://www.tweag.io/blog/2020-08-06-mcmc-intro3/"
              target="_blank"
              className="transition duration-300 hover:opacity-50"
            >
              <i className="fas fa-chevron-right ml-2 mr-5"></i>
              Hamiltonian Monte Carlo
            </a>
          </FlexCol>
        </FlexCol>
      </FlexCol>
    </div>
    <Button href="/job" className="bg-purple-600 hover:bg-purple-700">
      Give it a whirl
    </Button>
  </FlexCol>
);

const CopyrightFooter = () => (
  <FlexCenter className="h-10 mx-10 text-xs md:mx-20 lg:mx-40">
    <div className="opacity-30">All rights reserved. Copyright © 2021 by</div>
    <a href="https://www.tweag.io/">
      <img
        src="/tweag_logo_footer.svg"
        className="h-3 ml-2 opacity-30 hover:opacity-60 transition duration-300"
      />
    </a>
  </FlexCenter>
);

export default function Home() {
  return (
    <Layout>
      <FlexCol
        between
        className="h-screen text-white bg-gradient-to-r from-purple-900 to-indigo-600 font-body"
      >
        <Container>
          <Navbar />
        </Container>
        <Container>
          <Heading />
        </Container>
        <CopyrightFooter />
      </FlexCol>
    </Layout>
  );
}
