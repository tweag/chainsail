import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import nookies from 'nookies';
import useSWR from 'swr';
import moment from 'moment';
import { Line } from '@reactchartjs/react-chart.js';
import { v4 as uuidv4 } from 'uuid';

import { verifyIdToken } from '../utils/firebaseAdmin';
import {
  Layout,
  FlexCol,
  FlexCenter,
  FlexRow,
  JobButton,
  Container,
  Navbar,
  ResultsLink,
} from '../components';
import { dateFormatter } from '../utils/date';
import fetcher from '../utils/fetcher';
import useWindowDimensions from '../utils/windowDimensions';
import { sm } from '../utils/breakPoints';

const NegLogPChart = ({ job, simulationRun, isMobile }) => {
  if (job && job.id) {
    const jobId = job.id;
    const { data, error } = useSWR(`/api/graphite/neglogp/${jobId}/${simulationRun}`, fetcher, {
      refreshInterval: 5000,
    });
    if (error) console.log(error);
    const ds = data && data.length > 0 ? data[0].datapoints.filter((d) => d[0]) : [];
    const chartData = {
      datasets: [
        {
          labels: ds ? ds.map((d) => moment.unix(d[1]).format()) : [],
          xAxisID: 'x',
          yAxisID: 'y',
          label: 'total negative log-probability',
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
            gridLines: { color: 'rgb(256,256,256,0.3)', drawTicks: false },
            ticks: {
              fontColor: 'rgb(256,256,256,0.6)',
              padding: 10,
            },
          },
        ],
        yAxes: [
          {
            id: 'y',
            ticks: {
              beginAtZero: true,
              fontColor: 'rgb(256,256,256,0.6)',
              padding: 10,
            },
            gridLines: { color: 'rgb(256,256,256,0.3)', drawTicks: false },
          },
        ],
      },
    };

    const jobRunOrStop =
      job.status == 'running' ||
      job.status == 'stopping' ||
      job.status == 'stopped' ||
      job.status == 'success';
    return (
      <FlexCenter
        className={`w-full lg:h-1/2 transition duration-300 ${
          jobRunOrStop ? 'opacity-100' : 'opacity-20'
        }`}
      >
        {!error && !isMobile && <Line data={chartData} options={options} width="5" height="1" />}
        {!error && isMobile && <Line data={chartData} options={options} width="1" height="1" />}
      </FlexCenter>
    );
  } else {
    return <></>;
  }
};

const AcceptanceRateChart = ({ job, simulationRun, isMobile }) => {
  if (job && job.id) {
    const jobId = job.id;
    const { data, error } = useSWR(
      `/api/graphite/acceptancerate/${jobId}/${simulationRun}`,
      fetcher,
      {
        refreshInterval: 10000,
      }
    );
    if (error) console.log(error);
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
    const giveReplicaLabel = (target) =>
      target
        .split('.')[2]
        .split('_')
        .map((r) => r.replace('replica', ''))
        .join('<>');
    const chartData = {
      labels: dss ? dss.map((ds) => giveReplicaLabel(ds.target)) : [],
      datasets: [
        {
          label: 'acceptance rate',
          data: dss ? dss.map((ds) => ds.acceptanceRate) : [],
          fill: false,
          backgroundColor: 'rgb(255, 99, 132)',
          borderColor: 'rgba(255, 99, 132, 0.5)',
          lineTension: 0,
        },
      ],
    };
    const options = {
      legend: {
        labels: {
          fontColor: 'rgb(256,256,256,0.6)',
        },
      },
      scales: {
        xAxes: [
          {
            offset: true,
            gridLines: { color: 'rgb(256,256,256,0.3)', drawTicks: false },
            ticks: {
              fontColor: 'rgb(256,256,256,0.6)',
              padding: 10,
            },
          },
        ],
        yAxes: [
          {
            ticks: {
              beginAtZero: true,
              fontColor: 'rgb(256,256,256,0.6)',
              padding: 10,
            },
            gridLines: {
              color: 'rgb(256,256,256,0.3)',
              drawTicks: false,
            },
          },
        ],
      },
    };

    const jobRunOrStop =
      job.status == 'running' ||
      job.status == 'stopping' ||
      job.status == 'stopped' ||
      job.status == 'success';

    return (
      <FlexCenter
        className={`w-full lg:h-1/2 transition duration-300 ${
          jobRunOrStop ? 'opacity-100' : 'opacity-20'
        }`}
      >
        {!error && !isMobile && <Line data={chartData} options={options} width="5" height="1" />}
        {!error && isMobile && <Line data={chartData} options={options} width="1" height="1" />}
      </FlexCenter>
    );
  } else {
    return <></>;
  }
};

const Logs = ({ job }) => {
  useEffect(() => {
    var element = document.getElementById('logs');
    element.scrollTop = element.scrollHeight;
  }, []);
  const jobId = job.id;
  const { data, error } = useSWR(`/api/graphite/logs/${jobId}`, fetcher, {
    refreshInterval: 10000,
  });
  const logs =
    data && data.length > 0 ? data : [{ data: 'Please start the job to see the logs!' }];
  if (error) console.log(error);
  return (
    <FlexCenter className="py-5 h-1/2">
      <div
        className="w-full h-64 p-5 overflow-auto text-white bg-gray-900 lg:h-full lg:p-8 rounded-xl"
        id="logs"
      >
        {logs.map((log) => (
          <div key={uuidv4()} className="my-3 break-words">
            <div className="text-sm">{log.data}</div>
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
      <FlexCenter className="p-5 bg-indigo-900 border-2 shadow-xl lg:p-8 border-gray-50 border-opacity-30 rounded-xl">
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
          <div>Results:</div>
          <ResultsLink signed_url={job.signed_url} />
          <div className="mt-3 col-span-2">
            <FlexCenter>
              <JobButton jobId={job.id} jobStatus={job.status} width="w-full" />
            </FlexCenter>
          </div>
        </div>
      </FlexCenter>
    );
  } else {
    return <></>;
  }
};

const Dash = ({ authed }) => {
  const router = useRouter();
  const { jobId } = router.query;
  const { data, error } = useSWR(`/api/job/get/${jobId}`, fetcher);
  if (error) console.log(error);
  const jobFound = !error && data && data.id;
  const jobNotFound = !error && data && !data.id;
  const job = jobFound ? data : undefined;
  const isLoading = !data;
  const runs = jobFound && data.controller_iterations ? data.controller_iterations : [];

  // Dropdown
  const [dropdownIsAcitve, setDropdownIsAcitve] = useState(false);
  const [simulationRun, setSimulationRun] = useState(undefined);

  useEffect(() => {
    if (runs.length > 0) setSimulationRun(runs[0]);
  }, [runs]);

  // To check if the screen is for mobile
  const { width } = useWindowDimensions();
  const isMobile = width <= sm;

  const Dropdown = () => (
    <div className="relative mt-10">
      <div
        className={`transition duration-300 ${
          runs.length > 0
            ? 'cursor-pointer opacity-60 hover:opacity-100'
            : 'select-none opacity-10'
        }`}
        onClick={() => setDropdownIsAcitve((s) => !s)}
      >
        <div>
          {dropdownIsAcitve ? (
            <i className="mr-1 fas fa-caret-square-up"></i>
          ) : (
            <i className="mr-1 fas fa-caret-square-down"></i>
          )}
          {simulationRun ? `Simulation run: ${simulationRun}` : 'Choose a simulation run'}
        </div>
      </div>
      <div
        className={`${
          dropdownIsAcitve ? 'visible' : 'hidden h-0'
        } absolute z-1 bg-gray-800 bg-opacity-50 mt-1 transition-all duration-300 w-48`}
      >
        {runs.map((r) => (
          <div
            key={uuidv4()}
            onClick={() => {
              setSimulationRun(r);
              setDropdownIsAcitve(false);
            }}
            className="px-4 py-2 cursor-pointer transition duration-300 hover:bg-purple-700"
          >
            {r}
          </div>
        ))}
      </div>
    </div>
  );

  const jobRunOrStop =
    jobFound &&
    (job.status == 'running' ||
      job.status == 'stopping' ||
      job.status == 'stopped' ||
      job.status == 'success');

  if (authed)
    return (
      <Layout>
        <FlexCol className="min-h-screen text-white lg:h-screen bg-gradient-to-r from-purple-900 to-indigo-600 font-body">
          <Navbar />
          {jobFound && (
            <FlexRow responsive className="w-full h-full">
              <FlexCol className="pt-20 mx-10 lg:w-1/3 lg:mx-20">
                <div className="p-5 mb-10 bg-indigo-900 border-2 shadow-xl lg:p-8 border-gray-50 border-opacity-30 rounded-xl">
                  The plot of the total negative log-probability of all replicas helps to monitor
                  sampling convergence. If it scatters around a fixed value, your target
                  distribution is, given good Replica Exchange acceptance rates, likely to be
                  sampled exhaustively.
                </div>
                <JobInfo jobId={jobId} />
                <Dropdown />
              </FlexCol>
              <FlexCol between className="p-10 lg:w-2/3">
                <NegLogPChart job={job} simulationRun={simulationRun} isMobile={isMobile} />
                <AcceptanceRateChart job={job} simulationRun={simulationRun} isMobile={isMobile} />
                <Logs job={job} />
              </FlexCol>
              {!jobRunOrStop && (
                <div className="fixed invisible w-2/3 text-3xl lg:visible left-1/3 opacity-80 h-2/3">
                  <FlexCenter className="w-full h-full">No data to plot</FlexCenter>
                </div>
              )}
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
                  <Link href="/results">
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
    nookies.set(context, 'latestPage', '/dash', {});
    return {
      redirect: {
        permanent: false,
        destination: '/login',
      },
    };
  }
}

export default Dash;
