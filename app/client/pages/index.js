import { Layout, Button, FlexCenter, FlexCol, Container, Navbar } from '../components';

const Heading = () => (
  <FlexCol center className="h-full">
    <div className="mb-10 text-5xl md:text-9xl">Resaas</div>
    <div className="mb-10 text-2xl lg:w-2/3 md:text-4xl md:mb-20">
      scalable, automatically-tuning, cloud-based replica exchange implementation
    </div>
    <div className="text-base md:text-xl lg:w-2/3 md:text-justify mb-7">
      Replica exchange runs multiple MCMC samplers in parallel, the required number of which
      strongly depends on the probability distribution at hand and can go into the the hundreds. The
      number of parallel samplers, each running in a separate process, can be iteratively optimized
      by upscaling the cluster on the cloud platform.
    </div>
    <Button href="/job" className="bg-purple-600 hover:bg-purple-500">
      Checkout more!
    </Button>
  </FlexCol>
);

const CopyrightFooter = () => (
  <FlexCenter className="h-10 mx-10 md:mx-20 lg:mx-40 text-xs">
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
