import { MCMC_STATS_NEGLOGP_URL } from '../../../../../utils/const';
import handleRequestResponse from '../../../../../utils/handleRequestResponse';

export default async (req, res) => {
  const { jobId, simulationRun } = req.query;
  const url = MCMC_STATS_NEGLOGP_URL(jobId, simulationRun);
  const method = 'GET';
  const checkAuth = false;
  await handleRequestResponse(req, res, url, method, checkAuth);
};

export const config = {
  api: {
    bodyParser: false,
  },
};
