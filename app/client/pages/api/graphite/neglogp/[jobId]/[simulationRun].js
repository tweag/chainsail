import { GRAPHITE_NEGLOGP_URL } from '../../../../../utils/const';
import handleRequestResponse from '../../../../../utils/handleRequestResponse';

export default async (req, res) => {
  const { jobId, simulationRun } = req.query;
  const url = GRAPHITE_NEGLOGP_URL(jobId, simulationRun);
  const method = 'GET';
  const checkAuth = false;
  handleRequestResponse(req, res, url, method, checkAuth);
};
