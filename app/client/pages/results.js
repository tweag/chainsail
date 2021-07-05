import useSWR from 'swr';
import nookies from 'nookies';
import { v4 as uuidv4 } from 'uuid';

import { verifyIdToken } from '../utils/firebaseAdmin';
import { Layout, FlexCenter, FlexCol, Navbar, Container, Link } from '../components';
import JobInfo from '../components/JobInfo';
import fetcher from '../utils/fetcher';
import { useState } from 'react';

const JobsTableForMobile = ({ data }) => {
  // To keep track of clicked job row
  const [activeJobId, setActiveJobId] = useState(undefined);

  // Table headers
  const headersName = ['', 'Id', 'Name', ''];
  const TableHeader = ({ children }) => (
    <th className="px-2 py-1 text-left lg:px-4 lg:py-2">{children}</th>
  );

  // Table Rows
  const TableRow = ({ row, activeJobId }) => {
    const job_name = JSON.parse(row.spec).name;
    return (
      <tr
        className={`hover:bg-gray-800 transition duration-100 cursor-pointer ${
          activeJobId == row.id ? 'bg-indigo-900' : ''
        }`}
        onClick={() => {
          // Only trigger the job row if it's not the latest chosen row
          if (activeJobId == row.id) {
            setActiveJobId(undefined);
          } else {
            setActiveJobId(row.id);
          }
        }}
      >
        <TableData>
          <FlexCenter className={`transform ${activeJobId == row.id ? 'rotate-90' : 'rotate-0'}`}>
            <i className="fas fa-arrow-right"></i>
          </FlexCenter>
        </TableData>
        <TableData d={row.id} />
        <TableData d={job_name} />
        <TableData className="w-36">
          <Link href={`/dash?jobId=${row.id}`}>
            <div className="w-32 py-1 text-center text-white bg-purple-600 rounded-lg cursor-pointer lg:transition lg:duration-100 hover:bg-purple-700">
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
      <JobInfo jobId={activeJobId} />
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
          <Navbar isMobile={isMobile} />
          <Container>
            <FlexCenter className="py-5 md:py-32">
              {error && <div>Failed to load. Please refresh the page.</div>}
              {!error && data && data.errno && <div>Failed to load. Please refresh the page.</div>}
              {!error && data == undefined && <div>Loading ...</div>}
              {!error && Array.isArray(data) && data.length == 0 && <div>no jobs created yet</div>}
              {!error && Array.isArray(data) && data.length > 0 && isMobile && (
                <JobsTableForMobile data={data} />
              )}
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
