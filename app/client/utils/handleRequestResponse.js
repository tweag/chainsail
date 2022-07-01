const handleRequestResponse = async function (
  req,
  res,
  url,
  method,
  content_type = 'application/json',
  checkAuth = true
) {
  if (method === 'POST' && content_type === 'multipart/form-data') {
    var multiparty = require('multiparty');
    var http = require('http');
    var util = require('util');
    var FormData = require('form-data');

    var form = new multiparty.Form();

    var fd = new FormData();
    const parseForm = (req) =>
      new Promise((resolve, reject) => {
        new multiparty.Form().parse(req, function (err, fields, files) {
          if (err) reject(err);
          resolve([fields, files]);
        });
      });

    const [fields, files] = await parseForm(req);
    for (var key in fields) {
	if (typeof(fields[key][0]) === 'string' || typeof(fields[key][0]) === 'number') {
	    fd.append(key, fields[key][0]);
	} else {
	    fd.append(key, JSON.stringify(fields[key][0]));
	}
    }
    var fs = require('fs');
    for (var file in files) {
      var file_obj = files[file][0];
      fd.append(
        'probability_definition',
        fs.readFileSync(file_obj.path),
        file_obj.originalFilename
      );
    }
      try {
      const response = await fetch(url, {
        method: 'POST',
        body: fd,
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
  } else {
    const requestOptions = {
      method: method,
      headers: {
        Authorization: checkAuth ? `Bearer ${req.cookies.token}` : undefined,
      },
    };

    try {
      const augmented_req = new Request(req, requestOptions);
      const response = await fetch(url, augmented_req);
      const res_body = await response.json();
      res.status(response.status).json(res_body);
    } catch (e) {
      console.log(e);
      res.status(400).send(e);
    }
  }
};

export default handleRequestResponse;
