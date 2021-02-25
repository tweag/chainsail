import { FLASK_URL, JOB_CREATION_ENDPOINT } from '../../../utils/const';

export default async (req, res) => {
  const { token } = req.cookies;
  const body = JSON.stringify(req.body);
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body,
  };
  try {
    const response = await fetch(`${FLASK_URL}${JOB_CREATION_ENDPOINT}`, requestOptions);
    const res_body = await response.json();
    res.status(response.status).json(res_body);
  } catch (e) {
    res.status(404).send({ message: 'Server not found!' });
  }
};
