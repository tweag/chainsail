import nookies from 'nookies';
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
  if (authed)
    return (
      <Layout>
        <div className="bg-gray-100 lg:h-screen font-body">
          <FlexCenter className="h-full">
            <Line data={data} options={options} />
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
