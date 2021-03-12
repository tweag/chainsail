import { GRAPHITE_ACCEPTANCE_RATE_URL } from '../../../../utils/const';
import handleRequestResponse from '../../../../utils/handleRequestResponse';

export default async (req, res) => {
  const { slug } = req.query;
  const jobId = slug[0];
  const simulationRun = slug[1];
  const url = GRAPHITE_ACCEPTANCE_RATE_URL(jobId, simulationRun);
  const method = 'GET';
  const checkAuth = false;
  handleRequestResponse(req, res, url, method, checkAuth);
};
