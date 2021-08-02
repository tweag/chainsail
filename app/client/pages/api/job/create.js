import { JOB_CREATION_URL } from '../../../utils/const';
import handleRequestResponse from '../../../utils/handleRequestResponse';

export default async (req, res) => {
  const url = JOB_CREATION_URL;
  const method = 'POST';
  await handleRequestResponse(req, res, url, method);
};
