import nookies from 'nookies';
import useSWR from 'swr';
import moment from 'moment';
import { Line } from '@reactchartjs/react-chart.js';

import { verifyIdToken } from '../utils/firebaseAdmin';
import { AnimatedPing, Layout, FlexCol, FlexCenter, Container } from '../components';

const data = {
  labels: ['1', '2', '3', '4', '5', '6'],
  datasets: [
    {
      label: '# of Votes',
      data: [12, 19, 3, 5, 2, 3],
      fill: false,
      backgroundColor: 'rgb(255, 99, 132)',
      borderColor: 'rgba(255, 99, 132, 0.2)',
    },
  ],
};

const options = {
  scales: {
    yAxes: [
      {
        ticks: {
          beginAtZero: true,
        },
      },
    ],
  },
};

const Dash = ({ authed }) => {
  const graphiteUrl =
    'http://localhost/render?target=test_job.replica4.negative_log_prob&format=json';

  const fetcher = (url) => fetch(url).then((res) => res.json());
  const { data, error } = useSWR(graphiteUrl, fetcher, {});
  const txs = data ? data[0].datapoints.filter((d) => d[0]) : [];
  console.log(txs);
  const logPData = {
    labels: txs ? txs.map((tx) => moment.unix(tx[1]).format()) : [],
    datasets: [
      {
        label: '# of Votes',
        data: txs ? txs.map((tx) => tx[0]) : [],
        fill: false,
        backgroundColor: 'rgb(255, 99, 132)',
        borderColor: 'rgba(255, 99, 132, 0.2)',
      },
    ],
  };

  if (authed)
    return (
      <Layout>
        <div className="bg-gray-100 lg:h-screen font-body">
          <FlexCenter className="h-full">
            {!error && <Line data={logPData} options={options} />}
          </FlexCenter>
        </div>
      </Layout>
    );
};

export async function getServerSideProps(context) {
  try {
    const cookies = nookies.get(context);
    const token = await verifyIdToken(cookies.token);
    const { uid, email } = token;
    return {
      props: { email, uid, authed: true },
    };
  } catch (err) {
    return {
      redirect: {
        permanent: false,
        destination: '/login',
      },
    };
  }
}

export default Dash;
