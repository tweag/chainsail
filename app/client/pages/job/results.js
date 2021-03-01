import useSWR from 'swr';
import moment from 'moment';
import nookies from 'nookies';

import { verifyIdToken } from '../../utils/firebaseAdmin';
import { AnimatedPing, Layout, FlexCol, FlexCenter, Navbar, Container } from '../../components';
import { GRAPHITE_URL, GRAPHITE_PORT } from '../../utils/const';

const JobButton = ({ jobId, jobStatus }) => {
  const isInitialized = jobStatus === 'initialized';
  const isRunning = jobStatus === 'running';
  const isPending = jobStatus === 'starting';
  return (
    <div
      className={`py-1 text-center rounded-lg lg:transition lg:duration-100 text-white w-32
	      ${isInitialized ? 'bg-green-800 hover:bg-green-900 cursor-pointer' : ''}
	      ${isRunning ? 'bg-red-800 hover:bg-red-900 cursor-pointer' : ''}
	      ${isPending ? 'bg-yellow-800' : ''}
	      `}
      onClick={() => {
        if (isInitialized) startJob(jobId);
        if (isRunning) stopJob(jobId);
      }}
    >
      {isInitialized && 'START'}
      {isRunning && 'STOP'}
      {isPending && (
        <div>
          <div className="inline-block mr-3">PENDING</div>
          <AnimatedPing />
        </div>
      )}
    </div>
  );
};

const startJob = (jobId) => {
  const body = JSON.stringify({ jobId });
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  };
  fetch('/api/job/start', requestOptions);
};

const stopJob = (jobId) => {
  const body = JSON.stringify({ jobId });
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  };
  fetch('/api/job/stop', requestOptions);
};

const JobsTable = ({ data }) => {
  const headersName = ['Id', 'Name', 'Created at', 'Finished at', 'Started at', 'Status', '', ''];
  const dateFormatter = (d) => {
    if (d) return moment(d).format('d MMM hh:mm');
    else return '---';
  };
  const TableHeader = ({ children }) => <th className="px-4 py-2 text-left ">{children}</th>;
  const TableRow = ({ row }) => {
    const job_name = JSON.parse(row.spec).name;
    const graphite_link = `${GRAPHITE_URL}:${GRAPHITE_PORT}/render?target=${job_name}.*&height=800&width=800&from=-5min`;
    return (
      <tr className="hover:bg-gray-800 transition duration-100">
        <TableData d={row.id} />
        <TableData d={job_name} />
        <TableData d={dateFormatter(row.created_at)} />
        <TableData d={dateFormatter(row.started_at_at)} />
        <TableData d={dateFormatter(row.finished_at)} />
        <TableData d={row.status} className="w-40" />
        <TableData className="w-48">
          <div className="w-32 py-1 text-center text-white bg-purple-600 rounded-lg cursor-pointer lg:transition lg:duration-100 hover:bg-purple-700">
            <a href={graphite_link}>SEE PLOTS!</a>
          </div>
        </TableData>
        <TableData className="w-48">
          <JobButton jobId={row.id} jobStatus={row.status} />
        </TableData>
      </tr>
    );
  };
  const TableData = ({ d, children, className }) => (
    <td
      className={`px-4 py-2 border-t-2 transition duration-100
		  ${className}`}
    >
      {d ? d : children}
    </td>
  );
  return (
    <div className="w-full overflow-hidden text-white bg-gray-900 rounded-lg shadow-xl">
      <table className="w-full">
        <tr className="bg-blue-900 hover:bg-blue-800">
          {headersName.map((h) => (
            <TableHeader>{h}</TableHeader>
          ))}
        </tr>
        {data
          .sort((a, b) => (a.id > b.id ? 1 : -1))
          .map((row) => (
            <TableRow row={row} />
          ))}
      </table>
    </div>
  );
};

const Results = ({ authed }) => {
  // Data fetching
  const fetcher = (url) => fetch(url).then((res) => res.json());
  const { data, error } = useSWR('/api/job/get-all', fetcher, {
    refreshInterval: 3000,
  });

  if (authed)
    return (
      <Layout>
        <Container className="text-white bg-gradient-to-r from-purple-900 to-indigo-600 lg:h-screen font-body">
          <Navbar />
          <FlexCenter className="py-5 md:py-32">
            {error && <div>Failed to load. Please refresh the page.</div>}
            {!error && (data == undefined || data.length == 0) && <div>Loading...</div>}
            {data != undefined && data.length > 0 && <JobsTable data={data} />}
          </FlexCenter>
        </Container>
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

export default Results;
