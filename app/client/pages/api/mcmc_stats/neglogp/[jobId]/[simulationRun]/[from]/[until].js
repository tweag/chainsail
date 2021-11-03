import { GRAPHITE_NEGLOGP_URL } from '../../../../../../../utils/const';
import handleRequestResponse from '../../../../../../../utils/handleRequestResponse';

export default async (req, res) => {
  const { jobId, simulationRun, from, until } = req.query;
  const url = GRAPHITE_NEGLOGP_URL(jobId, simulationRun, from, until);
  console.log(url);
  const method = 'GET';
  const checkAuth = false;
  await handleRequestResponse(req, res, url, method, checkAuth);
};
