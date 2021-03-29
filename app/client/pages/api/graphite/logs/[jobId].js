import { GRAPHITE_LOGS_URL } from '../../../../utils/const';
import handleRequestResponse from '../../../../utils/handleRequestResponse';

export default async (req, res) => {
  const { jobId } = req.query;
  const url = GRAPHITE_LOGS_URL(jobId);
  const method = 'GET';
  const checkAuth = false;
  handleRequestResponse(req, res, url, method, checkAuth);
};
