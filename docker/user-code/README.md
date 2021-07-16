# Docker container for gRPC user code server

To build the image:
```bash
$ cd ../../
$ docker build -f docker/user-code/Dockerfile -t chainsail-user-code:latest .
```

To test the image locally, do something like
```bash
$ cd ../../examples/use-cases/mixture/
$ zip mixture.zip probability.py
$ python -m http.server &
$ docker run -it \
    -e USER_PROB_URL=http://localhost:8000/mixture.zip \
	-e USER_INSTALL_SCRIPT=/chainsail/test_install_script.sh \
	-v /home/simeon/projects/chainsail/docker/user-code/test_install_script.sh:/chainsail/test_install_script.sh \
	-e REMOTE_LOGGING_CONFIG_PATH=/chainsail/remote_logging.yaml \
	-v /home/simeon/projects/chainsail/docker/config_local/remote_logging.yaml:/chainsail/remote_logging.yaml \
	--network host \
	chainsail-user-code:latest
```
where you obviously will have to adapt the absolute paths. Then you can get yourself a `SafeUserPdf` object from `chainsail.common.pdfs` and use it to talk to the now dockerized gRPC server.
