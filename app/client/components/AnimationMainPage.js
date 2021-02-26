import { useSpring, animated } from 'react-spring';

function ReactSpring({ duration }) {
  const innerWidth = window.innerWidth;
  const outerWidth = window.outerWidth;
  const innerHeight = window.innerHeight;
  const outerHeight = window.outerHeight;

  const xmin = -5;
  const xmax = 5;
  const n_hills = Math.floor(Math.random() * 6) + 1;
  const n_hills_range = [...Array(n_hills).keys()];
  const means = n_hills_range.map(() => Math.random() * (xmax / 2 - xmin / 2) + xmin / 2);
  const sigmas = n_hills_range.map(() => Math.random() * 0.4 + 0.05);
  const pathFunction = (x) => {
    let y_unnorm = n_hills_range
      .map((i) => Math.exp(-Math.pow((x - means[i]) / sigmas[i], 2) / 2))
      .reduce((a, b) => a + b, 0);
    return y_unnorm / n_hills;
  };

  const offset = (Math.random() + 0.2) / 1.2;

  const eps = 0.3;
  const N = 300;
  const steps = [...Array(N).keys()];
  // t between 0 and 1
  const createPath = (t) => {
    let path = steps
      .map((i) => xmin + (xmax - xmin) * (t + eps * (i / N)))
      .filter((x) => x > xmin && x < xmax)
      .map((x) => {
        let y = pathFunction(x);
        let x_norm = ((x - xmin) / (xmax - xmin)) * innerWidth;
        let y_norm = -(y / (xmax - xmin)) * outerWidth + offset * outerHeight;
        return `${x_norm} ${y_norm}`;
      })
      .join(' L');
    path = 'M' + path;
    return path;
  };

  const props = useSpring({ t: 1, from: { t: 0 }, config: { duration } });

  return (
    <animated.path
      d={props.t.interpolate(createPath)}
      stroke="black"
      fill="none"
      stroke-width="5"
    ></animated.path>
  );
}

export default ReactSpring;
