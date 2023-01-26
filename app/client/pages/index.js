import { useCallback, useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import { Button, Container, FlexCenter, FlexCol, Layout, Navbar } from '../components';
import AnimationMainPage from '../components/AnimationMainPage';

const Heading = () => (
  <FlexCol center className="h-full">
    <div className="mb-10 text-5xl md:text-9xl">Chainsail</div>
    <div className="mb-10 text-2xl lg:w-2/3 md:text-4xl md:mb-20">
      sampling multimodal distributions made easy
    </div>
    <div className="text-base md:text-xl lg:w-2/3 md:text-justify mb-7">
      <FlexCol className="space-y-5">
        <div>
          Chainsail helps to sample multimodal distributions by implementing an automatically
          scaling Replica Exchange MCMC algorithm. All you need to provide is a Python module
          defining your probability density and its log-probability gradient.
        </div>
        <div>
          This beta version of Chainsail is free. Please{' '}
          <a
            href="mailto:support@chainsail.io"
            className="inline text-blue-400 hover:text-white transition duration-300"
          >
            e-mail us
          </a>{' '}
          to get your account authorized. Do ask us for a live demo!
        </div>
        <FlexCol className="space-y-2">
          <div>
            The{' '}
            <a
              href="https://github.com/tweag/chainsail-resources"
              className="inline text-blue-400 hover:text-white transition duration-300"
            >
              Chainsail resources repository
            </a>{' '}
            contains some background on the algorithms used in Chainsail and a complete
            walk-through. Also see our blog posts for details on the algorithms at work in
            Chainsail:
          </div>
          <FlexCol>
            <a
              href="https://www.tweag.io/blog/2020-10-28-mcmc-intro-4/"
              target="_blank"
              className="inline"
            >
              <i className="ml-2 mr-5 fas fa-chevron-right"></i>
              Replica Exchange
            </a>
            <a
              href="https://www.tweag.io/blog/2020-08-06-mcmc-intro3/"
              target="_blank"
              className="inline"
            >
              <i className="ml-2 mr-5 fas fa-chevron-right"></i>
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
    <div className="opacity-30">
      All rights reserved. Copyright © 2021-{new Date().getFullYear()} by
    </div>
    <a href="https://www.tweag.io/">
      <img
        src="/tweag_logo_footer.svg"
        className="h-3 ml-2 opacity-30 hover:opacity-60 transition duration-300"
      />
    </a>
  </FlexCenter>
);

const fireAnimation = () => {
  console.log('Animation fired');
  const parent = document.getElementById('animation-main-page');
  if (!parent) {
    return;
  }
  const id = Math.random(); //or some such identifier
  const div = document.createElement('div');
  div.id = id;
  parent.appendChild(div);
  const duration = 4000;
  ReactDOM.render(
    <svg className="fixed top-0 left-0 z-0 w-screen h-screen">
      <AnimationMainPage duration={duration} />
    </svg>,
    document.getElementById(id)
  );
  setTimeout(() => {
    const div_to_del = document.getElementById(id);
    if (div_to_del) {
      ReactDOM.unmountComponentAtNode(div_to_del);
      div_to_del.remove();
    }
  }, 6000);
};

export default function Home({ isMobile }) {
  // use `toggleAnim` to set whether the animation should be enabled or not
  const [anim, setAnim] = useState(null);
  const toggleAnim = useCallback(
    (doAnim) => {
      // should do anim, but it is not currently activated
      if (doAnim && anim === null) {
        console.log('Animation is now enabled');
        const newAnim = setInterval(() => {
          fireAnimation();
        }, 3000);
        setAnim(newAnim);
      }
      // should not do anim but is currently activated
      if (!doAnim && anim !== null) {
        console.log('Animation is now disabled');
        clearInterval(anim);
        setAnim(null);
      }
    },
    [anim]
  );

  useEffect(() => {
    // disable animation on mobile screen
    toggleAnim(!isMobile);
    return () => toggleAnim(false);
  }, [isMobile]);
  return (
    <Layout>
      <FlexCol
        between
        className="min-h-screen text-white bg-gradient-to-r opacity-95 from-purple-900 to-indigo-600 font-body"
      >
        <Navbar isMobile={isMobile} />
        <Container>
          <Heading />
        </Container>
        <CopyrightFooter />
      </FlexCol>
      <div
        id="animation-main-page"
        className="fixed top-0 left-0 w-screen h-screen"
        style={{ zIndex: -1 }}
      ></div>
    </Layout>
  );
}
