// Next.js API route support: https://nextjs.org/docs/api-routes/introduction

const FLASK_URL = process.env.FLASK_URL || 'http://127.0.0.1:5000';
const JOB_CREATION_ENDPOINT = '/job';

export default async (req, res) => {
  const token = '';
  const body = req.body;
  const requestOptions = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body,
  };
  const response = await fetch(`${FLASK_URL}${JOB_CREATION_ENDPOINT}`, requestOptions);
  res.statusCode = 200;
  res.json(response);
};
