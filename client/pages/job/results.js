import { useState } from 'react';
import useSWR from 'swr';
import { Layout, FlexCol, FlexCenter, Navbar, Container } from '../../components';

const Table = ({ data }) => {
  const headers = data.length != 0 ? Object.keys(data[0]) : [];
  const TableRow = ({ children }) => (
    <tr className="hover:bg-gray-700 transition duration-100">{children}</tr>
  );
  const TableHeader = ({ children }) => <th className="px-4 py-2 text-left ">{children}</th>;
  const TableData = ({ children }) => (
    <td className="px-4 py-2 border-t-2 transition duration-100">{children}</td>
  );
  return (
    <div className="w-full overflow-hidden text-white bg-gray-900 rounded-lg shadow-xl">
      <table className="w-full">
        <tr className="bg-blue-900 hover:bg-blue-800">
          {headers.map((h) => (
            <TableHeader>{h}</TableHeader>
          ))}
        </tr>
        {data.map((d) => (
          <TableRow>
            {Object.values(d).map((v) => (
              <TableData>{v}</TableData>
            ))}
          </TableRow>
        ))}
      </table>
    </div>
  );
};

export default function Job() {
  // Data fetching
  const FLASK_URL = process.env.FLASK_URL || 'http://127.0.0.1:5000';
  const JOBS_LIST_ENDPOINT = '/jobs';
  const fetcher = (url) => fetch(url).then((res) => res.json());
  const { data, error } = useSWR(`${FLASK_URL}${JOBS_LIST_ENDPOINT}`, fetcher, {
    refreshInterval: 1000,
  });

  if (error) return <div>failed to load</div>;

  return (
    <Layout>
      <Container className="text-white bg-gradient-to-r from-purple-900 to-indigo-600">
        <FlexCol between className="lg:h-screen">
          <Navbar />
          <FlexCenter className="w-full h-full py-5 md:py-20"></FlexCenter>
        </FlexCol>
      </Container>
    </Layout>
  );
}
