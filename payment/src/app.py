import sys
import os

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb'))
sys.path.insert(0, grpc_path)
import common_pb2 as common  # noqa
import common_pb2_grpc as common_grpc  # noqa

import grpc  # noqa
from concurrent import futures  # noqa


class PaymentService(common_grpc.TransactionService):
    def __init__(self):
        self.prepared = False

    def Prepare(self, request, context):
        self.prepared = True
        return common.PrepareResponse(ready=True)

    def Commit(self, request, context):
        if self.prepared:
            print(f"Payment successfully processed for order: {request.order_id}")
            self.prepared = False
        return common.CommitResponse(success=True)

    def Abort(self, request, context):
        self.prepared = False
        print("Payment aborted for", request.order_id)
        return common.AbortResponse(aborted=True)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    common_grpc.add_TransactionServiceServicer_to_server(
        PaymentService(), server)
    port = "50051"
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started. Listening on port 50051.")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
