import useSWR from 'swr';
import nookies from 'nookies';
import { v4 as uuidv4 } from 'uuid';

import { verifyIdToken } from '../utils/firebaseAdmin';
import {
  Layout,
  FlexCenter,
  FlexCol,
  JobButton,
  Navbar,
  Container,
  Link,
  ResultsLink,
} from '../components';
import { dateFormatter } from '../utils/date';
import fetcher from '../utils/fetcher';

const JobsTable = ({ data }) => {
  const headersName = [
    'Id',
    'Name',
    'Created at',
    'Started at',
    'Finished at',
    'Results',
    'Status',
    '',
    '',
  ];
  const TableHeader = ({ children }) => (
    <th className="px-2 py-1 text-left lg:px-4 lg:py-2">{children}</th>
  );
  const TableRow = ({ row }) => {
    const job_name = JSON.parse(row.spec).name;
    return (
      <tr className="hover:bg-gray-800 transition duration-100">
        <TableData d={row.id} />
        <TableData d={job_name} />
        <TableData d={dateFormatter(row.created_at)} />
        <TableData d={dateFormatter(row.started_at)} />
        <TableData d={dateFormatter(row.finished_at)} />
        <TableData className="w-48">
          <ResultsLink signed_url={row.signed_url} width="w-20 lg:w-32" />
        </TableData>
        <TableData d={row.status} className="w-40" />
        <TableData className="w-48">
          <Link href={`/dash?jobId=${row.id}`}>
            <div className="w-16 py-1 text-center text-white bg-purple-600 rounded-lg cursor-pointer lg:w-32 lg:transition lg:duration-100 hover:bg-purple-700">
              dash site
            </div>
          </Link>
        </TableData>
        <TableData className="w-48">
          <JobButton jobId={row.id} jobStatus={row.status} width="w-24 lg:w-32" />
        </TableData>
      </tr>
    );
  };
  const TableData = ({ d, children, className }) => (
    <td
      className={`px-2 py-1 text-left lg:px-4 lg:py-2 border-t-2
		  ${className}`}
    >
      {d ? d : children}
    </td>
  );
  return (
    <div className="w-full overflow-x-auto text-xs text-white bg-gray-900 rounded-lg shadow-xl lg:text-base">
      <table className="w-full">
        <thead>
          <tr className="bg-blue-900 hover:bg-blue-800">
            {headersName.map((h) => (
              <TableHeader key={uuidv4()}>{h}</TableHeader>
            ))}
          </tr>
        </thead>
        <tbody>
          {data
            .sort((a, b) => (a.id > b.id ? 1 : -1))
            .map((row) => (
              <TableRow row={row} key={uuidv4()} />
            ))}
        </tbody>
      </table>
    </div>
  );
};

const Results = ({ authed, isMobile }) => {
  // Data fetching
  const { data, error } = useSWR('/api/job/get-all', fetcher, {
    refreshInterval: 3000,
  });
  if (error) console.log(error);

  if (authed)
    return (
      <Layout>
        <FlexCol className="min-h-screen text-white lg:h-screen bg-gradient-to-r from-purple-900 to-indigo-600 font-body">
          <Navbar />
          <Container>
            <FlexCenter className="py-5 md:py-32">
              {error && <div>Failed to load. Please refresh the page.</div>}
              {!error && data && data.errno && <div>Failed to load. Please refresh the page.</div>}
              {!error && data == undefined && <div>Loading ...</div>}
              {!error && Array.isArray(data) && data.length == 0 && <div>no jobs created yet</div>}
              {!error && Array.isArray(data) && data.length > 0 && <JobsTable data={data} />}
            </FlexCenter>
          </Container>
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
    nookies.set(context, 'latestPage', '/results', {});
    return {
      redirect: {
        permanent: false,
        destination: '/login',
      },
    };
  }
}

export default Results;
