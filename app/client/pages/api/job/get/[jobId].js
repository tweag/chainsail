import { FLASK_URL, JOB_GET_ENDPOINT } from '../../../../utils/const';
import handleRequestResponse from '../../../../utils/handleRequestResponse';

export default async (req, res) => {
  const { jobId } = req.query;
  const url = `${FLASK_URL}${JOB_GET_ENDPOINT(jobId)}`;
  const method = 'GET';
  handleRequestResponse(req, res, url, method);
};
