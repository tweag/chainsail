import useSWR from 'swr';
import moment from 'moment';
import { Layout, FlexCol, FlexCenter, Navbar, Container } from '../../components';

const FLASK_URL = process.env.FLASK_URL || 'http://127.0.0.1:5000';

const StartJobButton = ({ jobId }) => {
  return (
    <div
      className={
        'py-1 text-center bg-purple-900 rounded-lg cursor-pointer lg:transition lg:duration-100 hover:bg-purple-700 text-white'
      }
      onClick={() => startJob(jobId)}
    >
      START
    </div>
  );
};

const startJob = (jobId) => {
  const JOB_START_ENDPOINT = `/job/${jobId}/start`;
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  };
  fetch(`${FLASK_URL}${JOB_START_ENDPOINT}`, requestOptions);
};

const JobsTable = ({ data }) => {
  const headersName = [
    'Id',
    'Name',
    'Created at',
    'Finished at',
    'Started at',
    //'spec' //TODO: should be checked if it's a good option to hide spec
    'Status',
    '',
  ];
  const dateFormatter = (d) => {
    if (d) return moment(d).format('d MMM hh:mm');
    else return '---';
  };
  const TableHeader = ({ children }) => <th className="px-4 py-2 text-left ">{children}</th>;
  const TableRow = ({ row }) => (
    <tr className="hover:bg-gray-700 transition duration-100">
      <TableData d={row.id} />
      <TableData d={row.name} />
      <TableData d={dateFormatter(row.created_at)} />
      <TableData d={dateFormatter(row.started_at_at)} />
      <TableData d={dateFormatter(row.finished_at)} />
      <TableData d={row.status} />
      <TableData>{row.status === 'initialized' && <StartJobButton jobId={row.id} />}</TableData>
    </tr>
  );
  const TableData = ({ d, children }) => (
    <td className="px-4 py-2 border-t-2 transition duration-100">{d ? d : children}</td>
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

export default function Job() {
  // Data fetching
  const JOBS_LIST_ENDPOINT = '/jobs';
  const fetcher = (url) => fetch(url).then((res) => res.json());
  const { data, error } = useSWR(`${FLASK_URL}${JOBS_LIST_ENDPOINT}`, fetcher, {
    refreshInterval: 3000,
  });

  return (
    <Layout>
      <Container className="text-white bg-gradient-to-r from-purple-900 to-indigo-600">
        <FlexCol between>
          <Navbar />
          <FlexCenter className="w-full h-full py-5 md:py-20">
            {error && <div>Failed to load. Please refresh the page.</div>}
            {(data == undefined || data.length == 0) && <div>Loading</div>}
            {data != undefined && data.length > 0 && <JobsTable data={data} />}
          </FlexCenter>
        </FlexCol>
      </Container>
    </Layout>
  );
}