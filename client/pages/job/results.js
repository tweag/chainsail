import { useState } from 'react';
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
  const [data, setData] = useState([]);

  const updateData = async () => {
    const FLASK_URL = process.env.FLASK_URL || 'http://127.0.0.1:5000';
    const JOBS_LIST_ENDPOINT = '/jobs';
    const requestOptions = {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    };
    let response = await fetch(`${FLASK_URL}${JOBS_LIST_ENDPOINT}`, requestOptions);
    let data = await response.json();
    console.log(data);
    if (response.status === 200) {
      setData(data);
    }
  };
  updateData();
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
