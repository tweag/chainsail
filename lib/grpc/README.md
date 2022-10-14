# chainsail.grpc

gRPC specs used in resaas. To re-generate run:

```shell
$ poetry run python -m grpc_tools.protoc \
           -I ./protos \
           --python_out=./chainsail/grpc \
           --grpc_python_out=./chainsail/grpc \
           ./protos/*.proto
```
After that, fix the second import in all `*_grpc.py` files by prepending a `chainsail.grpc.`.
