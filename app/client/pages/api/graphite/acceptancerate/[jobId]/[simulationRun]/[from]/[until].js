import { GRAPHITE_ACCEPTANCE_RATE_URL } from '../../../../../../../utils/const';
import handleRequestResponse from '../../../../../../../utils/handleRequestResponse';

export default async (req, res) => {
  const { jobId, simulationRun, from, until } = req.query;
  const url = GRAPHITE_ACCEPTANCE_RATE_URL(jobId, simulationRun, from, until);
  const method = 'GET';
  const checkAuth = false;
  await handleRequestResponse(req, res, url, method, checkAuth);
};
