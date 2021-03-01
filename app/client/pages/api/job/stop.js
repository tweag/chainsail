import { FLASK_URL, JOB_STOP_ENDPOINT } from '../../../utils/const';
import handleRequestResponse from '../../../utils/handleRequestResponse';

export default async (req, res) => {
  const url = `${FLASK_URL}${JOB_STOP_ENDPOINT(jobId)}`;
  const method = 'POST';
  handleRequestResponse(req, res, url, method);
};
