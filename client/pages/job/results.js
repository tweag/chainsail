import { useState } from 'react';
import { Layout, FlexCol, FlexCenter, Navbar, Container, FlexRow } from '../../components';

const jobsData = [
  {
    id: 'id1',
    name: 'name1',
    spec: 'spec1',
    status: 'status1',
    created_at: 'created_at1',
    started_at: 'started_at1',
    finished_at: 'finished_at1',
    nodes: 'node1',
  },
  {
    id: 'id2',
    name: 'name2',
    spec: 'spec2',
    status: 'status2',
    created_at: 'created_at2',
    started_at: 'started_at2',
    finished_at: 'finished_at2',
    nodes: 'node2',
  },
];

const Table = ({ data }) => {
  const headers = Object.keys(data[0]);
  const TableRow = ({ children }) => (
    <tr className="hover:bg-gray-700 transition duration-100">{children}</tr>
  );
  const TableHeader = ({ children }) => <th className="px-4 py-2 text-left ">{children}</th>;
  const TableData = ({ children }) => (
    <td className="px-4 py-2 border-t-2 transition duration-100">{children}</td>
  );
  return (
    <div className="w-full text-white bg-gray-900 shadow-xl rounded-lg overflow-hidden">
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
  const [data, setData] = useState(jobsData);
  return (
    <Layout>
      <Container className="text-white bg-gradient-to-r from-purple-900 to-indigo-600">
        <FlexCol between className="lg:h-screen">
          <Navbar />
          <FlexCenter className="w-full h-full py-5 md:py-20">
            <Table data={data} />
          </FlexCenter>
        </FlexCol>
      </Container>
    </Layout>
  );
}
