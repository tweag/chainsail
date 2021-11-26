import { useMemo, useCallback } from 'react';
import { useSpring, animated } from 'react-spring';

const xmin = -5;
const xmax = 5;
const eps = 0.3;
const N = 3000;

function ReactSpring({ duration }) {
  let interpolate = useMemo(() => {
    const { innerWidth, outerWidth, outerHeight } = window;
    const n_hills = Math.floor(Math.random() * 3) + 1;
    const n_hills_range = [...Array(n_hills).keys()];
    const means = n_hills_range.map(() => Math.random() * (xmax / 2 - xmin / 2) + xmin / 2);
    const sigmas = n_hills_range.map(() => Math.random() * 0.2 + 0.5);
    const offset = (Math.random() + 0.2) / 1.2;

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

    const globalPath = [...Array(Math.floor(N * (1 + eps))).keys()]
      .map((i) => i - Math.floor(N * eps))
      .map((i) => xmin + (xmax - xmin) * (i / N))
      .map((x) => {
        let y = pathFunction(x);
        let x_norm = ((x - xmin) / (xmax - xmin)) * innerWidth;
        let y_norm = -(y / (xmax - xmin)) * outerWidth + offset * outerHeight;
        return `${x_norm} ${y_norm}`;
      });
    return (t) => {
      let path = globalPath.slice(Math.floor(t * N), Math.floor((t + eps) * N)).join(' L');
      if (path.length === 0) {
        return 'M' + globalPath[globalPath.length - 1];
      }
      return 'M' + path;
    };
  }, []);

  const props = useSpring({ t: 1 + eps, from: { t: 0 }, config: { duration } });
  const d = useMemo(() => props.t.interpolate(interpolate), [interpolate]);

  return <animated.path d={d} stroke="black" fill="none" strokeWidth="5"></animated.path>;
}

export default ReactSpring;
