If you ever changed `health_check.proto` make sure to update the corresponding python classes with
running:

```bash
python3 -m grpc_tools.protoc -I ./ --python_out=. --grpc_python_out=. health_check.proto
```
