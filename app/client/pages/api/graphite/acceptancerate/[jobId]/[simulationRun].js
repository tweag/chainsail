import { GRAPHITE_ACCEPTANCE_RATE_URL } from '../../../../../utils/const';
import handleRequestResponse from '../../../../../utils/handleRequestResponse';

export default async (req, res) => {
  const { jobId, simulationRun } = req.query;
  const url = GRAPHITE_ACCEPTANCE_RATE_URL(jobId, simulationRun);
  const method = 'GET';
  const checkAuth = false;
  await handleRequestResponse(req, res, url, method, checkAuth);
};
