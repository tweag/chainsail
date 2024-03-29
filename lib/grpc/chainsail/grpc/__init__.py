from chainsail.grpc.health_checking_pb2 import HealthCheckRequest, HealthCheckResponse
from chainsail.grpc.health_checking_pb2_grpc import (
    HealthServicer,
    HealthStub,
    add_HealthServicer_to_server,
)


class Health(HealthServicer):
    def __init__(self, callback):
        super(Health, self).__init__()
        self.callback = callback

    def Check(self, request, context):
        status = self.callback()
        return HealthCheckResponse(status=status)
