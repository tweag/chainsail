import { GRAPHITE_LOGS_URL } from '../../../utils/const';
import handleRequestResponse from '../../../utils/handleRequestResponse';

export default async (req, res) => {
  const url = GRAPHITE_LOGS_URL;
  const method = 'GET';
  handleRequestResponse(req, res, url, method);
};
