import time
from flask import Flask, request, jsonify
import grpc
import json
import uuid
import os
import sys
from flask_cors import CORS
import redis

# Import gRPC stubs.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
order_queue_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/order_queue'))
sys.path.insert(0, order_queue_grpc_path)
import order_queue_pb2 as order_queue  # noqa: E402
import order_queue_pb2_grpc as order_queue_grpc  # noqa: E402

# Connect to Redis and poll for result
r = redis.Redis(host='redis', port=6379, decode_responses=True)

app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})


def send_to_queue(data, vc):
    with grpc.insecure_channel('order_queue:50054') as channel:
        stub = order_queue_grpc.OrderQueueStub(channel)
        req = order_queue.QueueOrderRequest()
        req.order_id = data["orderId"]
        req.payload = json.dumps(data)
        req.vector_clock.update(vc)
        stub.Enqueue(req)


@app.route("/checkout", methods=["POST"])
def checkout():
    print("Received request to /checkout")
    data = json.loads(request.data)
    order_id = str(uuid.uuid4())
    data["orderId"] = order_id
    vc = {"orchestrator": 1}
    send_to_queue(data, vc)

    result_key = f"result:{order_id}"
    timeout = 10
    for _ in range(timeout):
        if r.exists(result_key):
            result = json.loads(r.get(result_key))
            r.delete(result_key)
            break
        time.sleep(1)
    else:
        return jsonify({"error": "Timeout waiting for order result"}), 504

    order_status_response = {
        'orderId': order_id,
        'status': 'Order Approved' if result.get("status") == "approved" else 'Order Rejected',
        'suggestedBooks': result.get("suggestedBooks", [])
    }

    return jsonify(order_status_response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
