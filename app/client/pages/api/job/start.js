import { JOB_START_URL } from '../../../utils/const';
import handleRequestResponse from '../../../utils/handleRequestResponse';

export default async (req, res) => {
  const { jobId } = req.body;
  const url = JOB_START_URL(jobId);
  const method = 'POST';
  handleRequestResponse(req, res, url, method);
};
