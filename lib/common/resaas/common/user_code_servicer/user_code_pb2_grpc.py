# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import user_code_pb2 as user__code__pb2


class UserCodeServicerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.LogProb = channel.unary_unary(
                '/UserCodeServicer/LogProb',
                request_serializer=user__code__pb2.LogProbRequest.SerializeToString,
                response_deserializer=user__code__pb2.LogProbResponse.FromString,
                )
        self.LogProbGradient = channel.unary_unary(
                '/UserCodeServicer/LogProbGradient',
                request_serializer=user__code__pb2.LogProbGradientRequest.SerializeToString,
                response_deserializer=user__code__pb2.LogProbGradientResponse.FromString,
                )
        self.InitialState = channel.unary_unary(
                '/UserCodeServicer/InitialState',
                request_serializer=user__code__pb2.InitialStateRequest.SerializeToString,
                response_deserializer=user__code__pb2.InitialStateResponse.FromString,
                )


class UserCodeServicerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def LogProb(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def LogProbGradient(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def InitialState(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_UserCodeServicerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'LogProb': grpc.unary_unary_rpc_method_handler(
                    servicer.LogProb,
                    request_deserializer=user__code__pb2.LogProbRequest.FromString,
                    response_serializer=user__code__pb2.LogProbResponse.SerializeToString,
            ),
            'LogProbGradient': grpc.unary_unary_rpc_method_handler(
                    servicer.LogProbGradient,
                    request_deserializer=user__code__pb2.LogProbGradientRequest.FromString,
                    response_serializer=user__code__pb2.LogProbGradientResponse.SerializeToString,
            ),
            'InitialState': grpc.unary_unary_rpc_method_handler(
                    servicer.InitialState,
                    request_deserializer=user__code__pb2.InitialStateRequest.FromString,
                    response_serializer=user__code__pb2.InitialStateResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'UserCodeServicer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class UserCodeServicer(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def LogProb(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/UserCodeServicer/LogProb',
            user__code__pb2.LogProbRequest.SerializeToString,
            user__code__pb2.LogProbResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def LogProbGradient(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/UserCodeServicer/LogProbGradient',
            user__code__pb2.LogProbGradientRequest.SerializeToString,
            user__code__pb2.LogProbGradientResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def InitialState(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/UserCodeServicer/InitialState',
            user__code__pb2.InitialStateRequest.SerializeToString,
            user__code__pb2.InitialStateResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
