import { useSpring, animated } from 'react-spring';

function ReactSpring({ duration }) {
  const innerWidth = window.innerWidth;
  const outerWidth = window.outerWidth;
  const innerHeight = window.innerHeight;
  const outerHeight = window.outerHeight;

  const xmin = -5;
  const xmax = 5;
  const n_hills = Math.floor(Math.random() * 3) + 1;
  const n_hills_range = [...Array(n_hills).keys()];
  const means = n_hills_range.map(() => Math.random() * (xmax / 2 - xmin / 2) + xmin / 2);
  const sigmas = n_hills_range.map(() => Math.random() * 0.2 + 0.5);
  const pathFunction = (x) => {
    if (x >= xmin) {
      let y_unnorm = n_hills_range
        .map((i) => (1 / sigmas[i]) * Math.exp(-Math.pow((x - means[i]) / sigmas[i], 2) / 2))
        .reduce((a, b) => a + b, 0);
      return y_unnorm / n_hills;
    } else {
      return 0;
    }
  };

  const N = 3000;
  const eps = 0.3;
  const offset = (Math.random() + 0.2) / 1.2;
  let globalPath = [...Array(Math.floor(N * (1 + eps))).keys()]
    .map((i) => i - Math.floor(N * eps))
    .map((i) => xmin + (xmax - xmin) * (i / N))
    .map((x) => {
      let y = pathFunction(x);
      let x_norm = ((x - xmin) / (xmax - xmin)) * innerWidth;
      let y_norm = -(y / (xmax - xmin)) * outerWidth + offset * outerHeight;
      return `${x_norm} ${y_norm}`;
    });
  let interpolate = (t) => {
    let path = globalPath.slice(Math.floor(t * N), Math.floor((t + eps) * N)).join(' L');
    path = 'M' + path;
    return path;
  };

  const props = useSpring({ t: 1, from: { t: 0 }, config: { duration } });

  return (
    <animated.path
      d={props.t.interpolate(interpolate)}
      stroke="black"
      fill="none"
      stroke-width="5"
    ></animated.path>
  );
}

export default ReactSpring;
