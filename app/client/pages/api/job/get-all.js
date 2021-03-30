import { JOBS_LIST_URL } from '../../../utils/const';
import handleRequestResponse from '../../../utils/handleRequestResponse';

export default async (req, res) => {
  const url = JOBS_LIST_URL;
  const method = 'GET';
  handleRequestResponse(req, res, url, method);
};
