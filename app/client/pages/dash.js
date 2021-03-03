import Link from 'next/link';
import nookies from 'nookies';
import useSWR from 'swr';
import moment from 'moment';
import { Line } from '@reactchartjs/react-chart.js';

import { verifyIdToken } from '../utils/firebaseAdmin';
import { AnimatedPing, Layout, FlexCol, FlexCenter, Container, FlexRow } from '../components';
import { getJob } from '../utils/handleJob';
import { GRAPHITE_URL, GRAPHITE_PORT } from '../utils/const';

const options = {
  scales: {
    xAxes: [
      {
        id: 'x',
        type: 'time',
        time: { minUnit: 'second' },
        gridLines: { color: 'rgb(256,256,256,0.3)' },
        ticks: {
          fontColor: 'rgb(256,256,256,0.6)',
        },
      },
    ],
    yAxes: [
      {
        id: 'y',
        ticks: {
          beginAtZero: true,
          fontColor: 'rgb(256,256,256,0.6)',
        },
        gridLines: { color: 'rgb(256,256,256,0.3)' },
      },
    ],
  },
};

const giveChartData = (data) => {
  const ds = data && data.length > 0 ? data[0].datapoints.filter((d) => d[0]) : [];
  return {
    datasets: [
      {
        xAxisID: 'x',
        yAxisID: 'y',
        label: 'log p',
        data: ds
          ? ds.map((d) => {
              return { x: moment.unix(d[1]).format(), y: parseFloat(d[0]).toPrecision(2) };
            })
          : [],
        fill: false,
        backgroundColor: 'rgb(255, 99, 132)',
        borderColor: 'rgba(255, 99, 132, 0.5)',
      },
    ],
  };
};
const fetcher = (url) => fetch(url).then((res) => res.json());

const Chart = ({ jobId }) => {
  const graphiteUrl = `${GRAPHITE_URL}:${GRAPHITE_PORT}/render?target=aggregate(${jobId}.*.negative_log_prob,'average')&format=json&from=-5min`;
  const { data, error } = useSWR(graphiteUrl, fetcher, {
    refreshInterval: 10000,
  });
  const chartData = giveChartData(data);
  return (
    <FlexCenter className="w-full h-1/2">
      {!error && <Line data={chartData} options={options} width="3" height="1" />}
    </FlexCenter>
  );
};

const Logs = () => {
  const logsUrl = `${GRAPHITE_URL}:${GRAPHITE_PORT}/events/get_data?tags=log&from=-3hours&until=now`;

  //const { logs, errorLogs } = useSWR(logsUrl, fetcher, {
  //  refreshInterval: 10000,
  //});
  const logs = ['SDFSDFSFS', 'sDFSDFSDFSDF'];
  return (
    <FlexCenter className="py-5 h-1/2">
      <div className="w-full h-full p-8 overflow-auto text-white bg-gray-900 rounded-xl">
        <div className="mb-5">
          <AnimatedPing color="green-400" />
        </div>
        {logs.map((log, i) => (
          <div key={i} className="break-words">
            {log}
          </div>
        ))}
      </div>
    </FlexCenter>
  );
};

const Dash = ({ authed, job }) => {
  const jobId = job ? job.id : undefined;
  if (authed)
    return (
      <Layout>
        <div className="text-white bg-gradient-to-r from-purple-900 to-indigo-600 lg:h-screen font-body">
          {jobId && (
            <FlexRow className="w-full h-full">
              <FlexCenter className="w-1/3">Hello</FlexCenter>
              <FlexCol between className="w-2/3 p-10">
                <Chart jobId={jobId} />
                <Logs />
              </FlexCol>
            </FlexRow>
          )}
          {!jobId && (
            <FlexCenter className="w-full h-full">
              <FlexCol className="space-y-5">
                <div>
                  This job is not accessible for this user. Please refer to results page and choose
                  one of the jobs listed in the table.
                </div>
                <FlexCenter>
                  <Link href="/job/results">
                    <a className="px-6 py-2 w-72 text-base text-center bg-purple-700 rounded-lg cursor-pointer lg:transition lg:duration-300 hover:bg-purple-900 text-white">
                      Go back to results page!
                    </a>
                  </Link>
                </FlexCenter>
              </FlexCol>
            </FlexCenter>
          )}
        </div>
      </Layout>
    );
};

export async function getServerSideProps(context) {
  try {
    const cookies = nookies.get(context);
    const token = await verifyIdToken(cookies.token);
    const { uid, email } = token;
    const { jobId } = context.query;
    try {
      const res = await getJob(jobId);
      const job = res.json();
      return {
        props: { email, uid, authed: true, job },
      };
    } catch (err) {
      return {
        props: { email, uid, authed: true },
      };
    }
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
