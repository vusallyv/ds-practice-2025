import queue
import sys
import os

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb'))
sys.path.insert(0, grpc_path)

import common_pb2 as common  # noqa
from concurrent import futures  # noqa
import grpc  # noqa
import order_queue_pb2_grpc as order_queue_grpc  # noqa


class RequestWithPriority:
    def __init__(self, request):
        self.request = request
        # Negative so more product is prioritized
        self.priority = -sum([item.quantity for item in request.items])

    def __lt__(self, other):
        return self.priority < other.priority


class OrderQueueService(order_queue_grpc.OrderQueueServiceServicer):
    def __init__(self):
        self._queue = queue.PriorityQueue()

    def Enqueue(self, request, context):
        self._queue.put(RequestWithPriority(request))
        return common.Empty()

    def Dequeue(self, request, context):
        try:
            request = self._queue.get(timeout=2).request
            return request
        except queue.Empty:
            context.abort(grpc.StatusCode.ABORTED, 'Queue empty')


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())
    order_queue_grpc.add_OrderQueueServiceServicer_to_server(
        OrderQueueService(), server)
    # Listen on port 50051
    port = "50051"
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print("Server started. Listening on port 50051.")
    # Keep thread alive
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
