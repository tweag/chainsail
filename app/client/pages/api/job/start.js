import { FLASK_URL, JOB_START_ENDPOINT } from '../../../utils/const';

export default async (req, res) => {
  const { token } = req.cookies;
  const { job_id } = req.body;
  const endpoint = JOB_START_ENDPOINT(job_id);
  const requestOptions = {
    method: 'POST',
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
