const handleRequestResponse = async function (
  req,
  res,
  url,
  method,
  content_type = 'application/json',
  checkAuth = true
) {
  const requestOptions = {
    method: method,
    headers: {
      'Content-Type': content_type,
      Authorization: checkAuth ? `Bearer ${req.cookies.token}` : undefined,
    },
  };

  try {
    const augmented_req = new Request(url, req);
    const response = await fetch(augmented_req, requestOptions);
    const res_body = await response.json();
    res.status(response.status).json(res_body);
  } catch (e) {
    res.status(400).send(e);
  }
};

export default handleRequestResponse;
