import useSWR from 'swr';
import nookies from 'nookies';
import { v4 as uuidv4 } from 'uuid';

import { verifyIdToken } from '../utils/firebaseAdmin';
import { Layout, FlexCenter, Navbar, Container, Link } from '../components';
import JobInfo from '../components/JobInfo';
import fetcher from '../utils/fetcher';
import { useState } from 'react';

const JobsTable = ({ data, activeJobId, setActiveJobId }) => {
  const headersName = ['Id', 'Name', ''];
  const TableHeader = ({ children }) => (
    <th className="px-2 py-1 text-left lg:px-4 lg:py-2">{children}</th>
  );
  const TableRow = ({ row, activeJobId }) => {
    const job_name = JSON.parse(row.spec).name;
    return (
      <tr
        className={`hover:bg-gray-800 transition duration-100 cursor-pointer ${
          activeJobId == row.id ? 'bg-gray-800' : ''
        }`}
        onClick={() => setActiveJobId(row.id)}
      >
        <TableData d={row.id} />
        <TableData d={job_name} />
        <TableData className="w-36">
          <Link href={`/dash?jobId=${row.id}`}>
            <div className="py-1 text-center text-white bg-purple-600 rounded-lg cursor-pointer w-32 lg:transition lg:duration-100 hover:bg-purple-700">
              dash site
            </div>
          </Link>
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
    <div className="w-full overflow-x-auto text-xs text-white bg-gray-900 rounded-lg shadow-xl md:w-2/3 lg:w-1/2 lg:text-base">
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
              <TableRow row={row} key={uuidv4()} activeJobId={activeJobId} />
            ))}
        </tbody>
      </table>
      <div className={`bg-gray-900 ${activeJobId ? 'p-5 border-t-2' : 'h-0'}`}>
        <JobInfo jobId={activeJobId} />
      </div>
    </div>
  );
};

const Results = ({ authed, isMobile }) => {
  // Data fetching
  const { data, error } = useSWR('/api/job/get-all', fetcher, {
    refreshInterval: 3000,
  });
  if (error) console.log(error);

  const [activeJobId, setActiveJobId] = useState(undefined);

  if (authed)
    return (
      <Layout>
        <Container className="min-h-screen text-white bg-gradient-to-r from-purple-900 to-indigo-600 font-body">
          <Navbar isMobile={isMobile} />
          <FlexCenter className="py-5 md:py-32">
            {error && <div>Failed to load. Please refresh the page.</div>}
            {!error && data && data.errno && <div>Failed to load. Please refresh the page.</div>}
            {!error && data == undefined && <div>Loading ...</div>}
            {!error && Array.isArray(data) && data.length == 0 && <div>no jobs created yet</div>}
            {!error && Array.isArray(data) && data.length > 0 && (
              <JobsTable data={data} activeJobId={activeJobId} setActiveJobId={setActiveJobId} />
            )}
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
