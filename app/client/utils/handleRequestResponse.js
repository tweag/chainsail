const handleRequestResponse = async function (req, res, url, method, checkAuth = true) {
  const requestOptions = {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: checkAuth ? `Bearer ${req.cookies.token}` : undefined,
    },
    body: method == 'POST' ? JSON.stringify(req.body) : undefined,
  };
  try {
    const response = await fetch(url, requestOptions);
    const res_body = await response.json();
    res.status(response.status).json(res_body);
  } catch (e) {
    res.status(400).send(e);
  }
};

export default handleRequestResponse;
