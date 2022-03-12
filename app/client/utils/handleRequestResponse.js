const handleRequestResponse = async function (
  req,
  res,
  url,
  method,
  content_type = 'application/json',
  checkAuth = true
) {
  var body = undefined;
  if (content_type == 'multipart/form-data') {
    // The body of the request is a string that contains form fields,
    // each with their appropriate Content-Type, and delimited by a
    // random string set by React. To create a multipart/form-data
    // request that can be parsed correctly by the server, the
    // boundary has to be part of the Content-Type header.
    // See
    // https://stackoverflow.com/questions/29539498/what-if-the-form-data-boundary-is-contained-in-the-attached-file
    // https://stackoverflow.com/questions/3508338/what-is-the-boundary-in-multipart-form-data
    // for some useful reading on this.
    // Usually, you can pass a FormData object directly to fetch, but
    // in this middleware here we have to recreate a proper request
    // from the string data we have in the request body and the proper
    // header.
    // So here we extract the boundary from the body of the request;
    // it is the first line minus two leading dashes ("-") and a
    // terminating CRLF (carriage return + next line).
    const boundary = req.body.split('\r')[0].slice(2);
    // Here we augment the content type with the boundary parameter
    content_type = content_type + ';boundary=' + boundary;
    body = req.body;
  } else if (content_type == 'application/json') {
    body = method == 'POST' ? JSON.stringify(req.body) : undefined;
  }
  const requestOptions = {
    method,
    headers: {
      'Content-Type': content_type,
      Authorization: checkAuth ? `Bearer ${req.cookies.token}` : undefined,
    },
    body: body,
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
