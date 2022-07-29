import { JOB_CREATION_URL } from '../../../utils/const';
import handleRequestResponse from '../../../utils/handleRequestResponse';

export default async (req, res) => {
  const url = JOB_CREATION_URL;
  const method = 'POST';
  await handleRequestResponse(req, res, url, method, 'multipart/form-data');
};

// Next.js's body parser doesn't handle multipart/form-data, so we deactivate
// the body parser here and parse the request manually using an external library
// in handleRequestResponse.
export const config = {
  api: {
    bodyParser: false,
  },
};
