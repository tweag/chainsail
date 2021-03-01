import { FLASK_URL, JOBS_LIST_ENDPOINT } from '../../../utils/const';
import handleRequestResponse from '../../../utils/handleRequestResponse';

export default async (req, res) => {
  const url = `${FLASK_URL}${JOBS_LIST_ENDPOINT}`;
  const method = 'GET';
  handleRequestResponse(req, res, url, method);
};
