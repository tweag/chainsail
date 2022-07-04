import { JOB_GET_URL } from '../../../../utils/const';
import handleRequestResponse from '../../../../utils/handleRequestResponse';

export default async (req, res) => {
  const { jobId } = req.query;
  const url = JOB_GET_URL(jobId);
  const method = 'GET';
  await handleRequestResponse(req, res, url, method);
};
