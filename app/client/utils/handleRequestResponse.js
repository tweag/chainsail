/*
This kind of middleware serves to encapsulate requests to the backend
and to add authentication headers.
*/

const handleRequestResponse = async function (
  req,
  res,
  url,
  method,
  content_type = 'application/json',
  checkAuth = true
) {
  var body = undefined;
  if (method === 'POST' && content_type === 'multipart/form-data') {
    /*
    req is a IncomingMessage (https://nodejs.org/api/http.html#class-httpincomingmessage)
    object (and _not_, despite of the name, a ClientRequest
    (https://nodejs.org/api/http.html#class-httpclientrequest)). It represents an in-progress
    request. To add authentication headers, we need to either modify the headers of req
    directly and "forward" it into a request to the backend.
    Now, if the IncomingMEssage has content type "multipart/form-data", we cannot access
    its `body` property without having an appropriate bodyParser. next.js's default body
    parser cannot parse `multipart/form-data` and thus the `body` attribute will be `undefined`.
    That's why we deactivate the body parser in the `job/create` API route. Instead of relying
    on a next.js-internal parser, we use the `multiparty` library that provides a convenient
    interface for parsing `multipart/form-data` content types. We thus parse the IncomingMessage
    body and create a new `FormData` object via the `form-data` library with exactly the same
    contents as before. Finally, we send the new `FormData` object, along with the authentication
    headers, to the backend.
    This jumps through way too many hoops and there must be a nicer solution, but I wasn't able to
    work well with the IncomingMessage stream-like object and stream it directly into a new request.
    So for now this has to do.
    */
    var multiparty = require('multiparty');
    var FormData = require('form-data');
    // File streams
    var fs = require('fs');

    var form = new multiparty.Form();

    var fd = new FormData();
    // Promified (returning a promise) `multipart/form-data` parsing
    // (https://github.com/pillarjs/multiparty/issues/166#issuecomment-1065491411)
    // Note that this downloads all files and stores them in a temporary directory.
    const parseForm = (req) =>
      new Promise((resolve, reject) => {
        new multiparty.Form().parse(req, function (err, fields, files) {
          if (err) reject(err);
          resolve([fields, files]);
        });
      });

    // parse form into fields and files
    const [fields, files] = await parseForm(req);
    // fill write form fields into new FormData object
    for (var field_name in fields) {
      // For reasons unknown to me, fields[key] is an array with a single entry instead of
      // the JSON value directly. So we have to access fields[key][0].
      var field_data = fields[field_name][0];
      if (field_data instanceof Array) {
        // Arrays cannot be appended to a FormData object. Instead, they have to be stringified.
        fd.append(field_name, JSON.stringify(field_data));
      } else {
        fd.append(field_name, field_data);
      }
    }
    // Now deal with the only file in the IncomingMessage
    if (Object.keys(files).length == 1) {
      // Again, no idea why this is an array instead of a single value
      var file_obj = files['probability_definition'][0];
      fd.append(
        'probability_definition',
        // Read file from disk
        fs.readFileSync(file_obj.path),
        file_obj.originalFilename
      );
    } else {
      var err_msg = 'Invalid number of files sent to job/create route';
      console.log(err_msg);
      res.status(400).send(err_msg);
      return;
    }
    body = fd;
  } else {
    // The body got parsed by the body parser, so we have to stringify it again
    body = method === 'POST' ? JSON.stringify(req.body) : undefined;
  }
  try {
    const response = await fetch(url, {
      method: method,
      body: body,
      headers: {
        Authorization: checkAuth ? `Bearer ${req.cookies.token}` : undefined,
      },
    });
    const res_body = await response.json();
    res.status(response.status).json(res_body);
  } catch (e) {
    console.log(e);
    res.status(400).send(e);
  }
};

export default handleRequestResponse;
