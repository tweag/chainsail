import { FLASK_URL, JOBS_LIST_ENDPOINT } from '../../../utils/const';

export default async (req, res) => {
  const { token } = req.cookies;
  const endpoint = JOBS_LIST_ENDPOINT;
  const requestOptions = {
    method: 'GET',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  };
  try {
    const response = await fetch(`${FLASK_URL}${endpoint}`, requestOptions);
    const res_body = await response.json();
    res.status(response.status).json(res_body);
  } catch (e) {
    res.status(404).send(e);
  }
};
