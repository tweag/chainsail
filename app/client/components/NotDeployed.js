import Layout from './Layout';
import { FlexCenter } from './Flex';

const NotDeployed = () => {
  return (
    <Layout>
      <FlexCenter className="min-h-screen text-white bg-gradient-to-r from-purple-900 to-indigo-600 font-body">
        <div>Chainsail is currently not deployed under this URL.</div>
      </FlexCenter>
    </Layout>
  );
};

export default NotDeployed;
