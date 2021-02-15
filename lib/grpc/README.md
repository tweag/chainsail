# resaas.grpc

gRPC specs used in resaas. To re-generate run:

```shell
$ poetry run python -m grpc_tools.protoc \
           -I ./protos \
           --python_out=./resaas/grpc \
           --grpc_python_out=./resaas/grpc \
           ./protos/*.proto
```
