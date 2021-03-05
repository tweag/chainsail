import Link from 'next/link';
import { useRouter } from 'next/router';
import nookies from 'nookies';
import useSWR from 'swr';
import moment from 'moment';
import { Bar, Line } from '@reactchartjs/react-chart.js';

import { verifyIdToken } from '../utils/firebaseAdmin';
import {
  AnimatedPing,
  Layout,
  FlexCol,
  FlexCenter,
  FlexRow,
  JobButton,
  Container,
  Navbar,
} from '../components';
import { GRAPHITE_URL, GRAPHITE_PORT } from '../utils/const';
import { dateFormatter } from '../utils/date';

const options = {
  legend: {
    labels: {
      fontColor: 'rgb(256,256,256,0.6)',
    },
  },
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

const fetcher = (url) => fetch(url).then((res) => res.json());

const NegLogPChart = ({ job }) => {
  if (job && job.id) {
    const jobSpec = JSON.parse(job.spec);
    const jobName = jobSpec.name;
    const graphiteUrl = `${GRAPHITE_URL}:${GRAPHITE_PORT}/render?target=aggregate(${jobName}.*.negative_log_prob,'sum')&format=json&from=-5min`;
    const { data, error } = useSWR(graphiteUrl, fetcher, {
      refreshInterval: 10000,
    });
    const ds = data && data.length > 0 ? data[0].datapoints.filter((d) => d[0]) : [];
    const chartData = {
      datasets: [
        {
          labels: ds ? ds.map((d) => moment.unix(d[1]).format()) : [],
          xAxisID: 'x',
          yAxisID: 'y',
          label: 'negative log-probability',
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
    return (
      <FlexCenter className="w-full h-1/2">
        {!error && <Line data={chartData} options={options} width="5" height="1" />}
      </FlexCenter>
    );
  } else {
    return <></>;
  }
};

const AcceptanceRateChart = ({ job }) => {
  if (job && job.id) {
    const jobSpec = JSON.parse(job.spec);
    const jobName = jobSpec.name;
    const graphiteUrl = `${GRAPHITE_URL}:${GRAPHITE_PORT}/render?target=${jobName}.replica*_replica*.acceptance_rate&format=json&from=-5min`;
    const { data, error } = useSWR(graphiteUrl, fetcher, {
      refreshInterval: 10000,
    });
    const dss =
      data && data.length > 0
        ? data.map((ds) => {
            let acceptanceRate;
            try {
              acceptanceRate = ds.datapoints.filter((d) => d[0]).pop()[0];
            } catch (err) {}
            return {
              acceptanceRate,
              target: ds.target,
            };
          })
        : [];
    const chartData = {
      labels: dss ? dss.map((ds) => ds.target.split('.')[1]) : [],
      datasets: [
        {
          label: 'acceptance rate',
          data: dss ? dss.map((ds) => ds.acceptanceRate) : [],
          fill: false,
          backgroundColor: 'rgb(255, 99, 132)',
          borderColor: 'rgba(255, 99, 132, 0.5)',
        },
      ],
    };
    const barOptions = {
      legend: {
        labels: {
          fontColor: 'rgb(256,256,256,0.6)',
        },
      },
      scales: {
        xAxes: [
          {
            gridLines: { color: 'rgb(256,256,256,0.3)' },
            ticks: {
              fontColor: 'rgb(256,256,256,0.6)',
            },
          },
        ],
        yAxes: [
          {
            ticks: {
              beginAtZero: true,
              fontColor: 'rgb(256,256,256,0.6)',
            },
            gridLines: { color: 'rgb(256,256,256,0.3)' },
          },
        ],
      },
    };

    return (
      <FlexCenter className="w-full h-1/2">
        {!error && <Bar data={chartData} options={barOptions} width="5" height="1" />}
      </FlexCenter>
    );
  } else {
    return <></>;
  }
};

const Logs = () => {
  //const logsUrl = `${GRAPHITE_URL}:${GRAPHITE_PORT}/events/get_data?tags=log&from=-3hours&until=now`;
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

const JobInfo = ({ jobId }) => {
  const { data } = useSWR(`/api/job/get/${jobId}`, fetcher, {
    refreshInterval: 3000,
  });
  if (data && data.id) {
    const job = data;
    const jobSpec = job.spec ? JSON.parse(job.spec) : {};
    return (
      <FlexCol className="w-1/3 pt-20">
        <div className="p-8 mx-20 mb-10 bg-indigo-900 border-2 shadow-xl border-gray-50 border-opacity-30 rounded-xl">
          The plot of the negative log-probability of your target distribution helps to monitor
          sampling convergence. If it scatters around a fixed value, your distribution is, given
          good Replica Exchange acceptance rates, likely sampled exhaustively.
        </div>
        <FlexCenter className="p-8 mx-20 bg-indigo-900 border-2 shadow-xl border-gray-50 border-opacity-30 rounded-xl">
          <div className="w-full grid grid-cols-2 gap-y-2">
            <div>Name:</div>
            <div>{jobSpec.name}</div>
            <div>Status: </div>
            <div>{job.status}</div>
            <div>Created at:</div>
            <div>{dateFormatter(job.created_at)}</div>
            <div>Started at:</div>
            <div>{dateFormatter(job.started_at)}</div>
            <div>Finished at:</div>
            <div>{dateFormatter(job.finished_at)}</div>
            <div className="mt-3 col-span-2">
              <FlexCenter>
                <JobButton jobId={job.id} jobStatus={job.status} width="w-full" />
              </FlexCenter>
            </div>
          </div>
        </FlexCenter>
      </FlexCol>
    );
  } else {
    return <></>;
  }
};

const Dash = ({ authed }) => {
  const router = useRouter();
  const { jobId } = router.query;
  const { data, error } = useSWR(`/api/job/get/${jobId}`, fetcher);
  const jobFound = !error && data && data.id;
  const jobNotFound = !error && data && !data.id;
  const isLoading = !data;

  if (authed)
    return (
      <Layout>
        <FlexCol className="text-white bg-gradient-to-r from-purple-900 to-indigo-600 lg:h-screen font-body">
          <Container>
            <Navbar />
          </Container>
          {jobFound && (
            <FlexRow className="w-full h-full">
              <JobInfo jobId={jobId} />
              <FlexCol between className="w-2/3 p-10">
                <NegLogPChart job={data} />
                <AcceptanceRateChart job={data} />
                <Logs />
              </FlexCol>
            </FlexRow>
          )}
          {jobNotFound && (
            <FlexCenter className="w-full h-full">
              <FlexCol className="space-y-5">
                <div>
                  This job is not accessible for this user. Please refer to results page and choose
                  one of the jobs listed in the table.
                </div>
                <FlexCenter>
                  <Link href="/job/results">
                    <a className="px-6 py-2 text-base text-center text-white bg-purple-700 rounded-lg cursor-pointer w-72 lg:transition lg:duration-300 hover:bg-purple-900">
                      Go back to results page!
                    </a>
                  </Link>
                </FlexCenter>
              </FlexCol>
            </FlexCenter>
          )}
          {isLoading && <FlexCenter className="w-full h-full">Loading ...</FlexCenter>}
        </FlexCol>
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
