import grpc
from concurrent import futures
import time
import redis
import json

import os
import sys

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
order_queue_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/order_queue'))
sys.path.insert(0, order_queue_grpc_path)

import order_queue_pb2 as queue_pb2  # noqa: E402
import order_queue_pb2_grpc as queue_grpc  # noqa: E402


class OrderQueueService(queue_grpc.OrderQueueServicer):
    def __init__(self):
        self.redis = redis.Redis(
            host='redis', port=6379, decode_responses=True)

    def Enqueue(self, request, context):
        self.redis.rpush("order_queue", json.dumps({
            "data": json.loads(request.payload),
            "vector_clock": dict(request.vector_clock)
        }))
        return queue_pb2.QueueOrderResponse(status="queued")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    queue_grpc.add_OrderQueueServicer_to_server(OrderQueueService(), server)
    server.add_insecure_port('[::]:50054')
    server.start()
    print("OrderQueue gRPC server started on port 50054")
    while True:
        time.sleep(5)


if __name__ == '__main__':
    serve()
