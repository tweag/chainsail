export default handleRequestResponse = function(req, res, url, method) {
  const { token } = req.cookies;
  const requestOptions = {
    method,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: (method == 'POST')? JSON.stringify(req.body): undefined,
  }
  try {
    const response = await fetch(url, requestOptions);
    const res_body = await response.json();
    res.status(response.status).json(res_body);
  } catch (e) {
    res.status(400).send(e);
  }
};

