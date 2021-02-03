# resaas.grpc

gRPC specs used in resaas. To re-generate run the following command
using the project's nix shell.

```shell
$ python -m grpc_tools.protoc \
           -I ./protos \
           --python_out=./resaas/grpc \
           --grpc_python_out=./resaas/grpc \
           ./protos/*.proto
```
