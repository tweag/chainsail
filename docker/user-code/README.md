# Docker container for gRPC user code server

To build the image:
```bash
$ cd ../../
$ docker build -f docker/user-code/Dockerfile -t resaas-user-code:latest .
```

To test the image locally, do something like
```bash
$ cd ../../examples/use-cases/mixture/
$ zip mixture.zip probability.py
$ python -m http.server &
$ docker run -it \
    -e USER_PROB_URL=http://localhost:8000/mixture.zip \
	-e USER_INSTALL_SCRIPT=/resaas/test_install_script.sh \
	-v /home/simeon/projects/resaas/docker/user-code/test_install_script.sh:/resaas/test_install_script.sh \
	-e REMOTE_LOGGING_CONFIG_PATH=/resaas/remote_logging.yaml \
	-v /home/simeon/projects/resaas/docker/config_local/remote_logging.yaml:/resaas/remote_logging.yaml \
	--network host \
	resaas-user-code:latest
```
where you obviously will have to adapt the absolute paths. Then you can get yourself a `SafeUserPdf` object from `resaas.common.pdfs` and use it to talk to the now dockerized gRPC server.
