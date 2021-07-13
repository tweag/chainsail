import { USER_CREATION_URL } from '../../../utils/const';
import handleRequestResponse from '../../../utils/handleRequestResponse';

export default async (req, res) => {
  const url = USER_CREATION_URL;
  const method = 'POST';
  handleRequestResponse(req, res, url, method);
};
