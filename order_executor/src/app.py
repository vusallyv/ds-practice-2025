import redis
import json
import time
import socket
from concurrent.futures import ThreadPoolExecutor
import os
import sys
# Import gRPC stubs.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/fraud_detection'))
sys.path.insert(0, fraud_detection_grpc_path)
import fraud_detection_pb2 as fraud_detection  # noqa: E402
import fraud_detection_pb2_grpc as fraud_detection_grpc  # noqa: E402
transaction_verification_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/transaction_verification'))
sys.path.insert(0, transaction_verification_grpc_path)
# Import gRPC stubs.
suggestions_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/suggestions'))
sys.path.insert(0, suggestions_grpc_path)
# Import gRPC stubs.
sys.path.insert(0, transaction_verification_grpc_path)
# Import gRPC stubs.
# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
import transaction_verification_pb2 as transaction_verification  # noqa: E402
import transaction_verification_pb2_grpc as transaction_verification_grpc  # noqa: E402
import suggestions_pb2 as suggestions  # noqa: E402
import suggestions_pb2_grpc as suggestions_grpc  # noqa: E402
import grpc  # noqa: E402


def merge_vector_clocks(*vcs):
    merged = {}
    for vc in vcs:
        for key, value in vc.items():
            merged[key] = max(merged.get(key, 0), value)
    return merged


def detect_fraud(data: dict, vc: dict):
    with grpc.insecure_channel('fraud_detection:50051') as channel:
        stub = fraud_detection_grpc.FraudServiceStub(channel)
        request_msg = fraud_detection.FraudRequest()
        request_msg.order_id = data["orderId"]
        request_msg.name = data["user"]["name"]
        request_msg.credit_card_number = data["creditCard"]["number"]
        request_msg.credit_card_expiration_date = data["creditCard"]["expirationDate"]
        request_msg.user_comment = data["userComment"]
        request_msg.items_length = str(len(data["items"]))
        request_msg.vector_clock.update(vc)
        response = stub.detect(request_msg)
    return response.is_fraud, dict(response.vector_clock)


def verify_transaction(data: dict, vc: dict):
    with grpc.insecure_channel('transaction_verification:50052') as channel:
        stub = transaction_verification_grpc.TransactionServiceStub(channel)
        request_msg = transaction_verification.TransactionRequest()
        request_msg.order_id = data["orderId"]
        request_msg.name = data["user"]["name"]
        request_msg.credit_card_number = data["creditCard"]["number"]
        request_msg.credit_card_expiration_date = data["creditCard"]["expirationDate"]
        request_msg.items_length = str(len(data["items"]))
        request_msg.vector_clock.update(vc)
        response = stub.verify(request_msg)
    return response.is_fraud, dict(response.vector_clock)


def suggest_books(data: dict, vc: dict):
    with grpc.insecure_channel('suggestions:50053') as channel:
        stub = suggestions_grpc.SuggestionsServiceStub(channel)
        request_msg = suggestions.SuggestionsRequest()
        request_msg.order_id = data["orderId"]
        request_msg.books = ','.join([item["name"] for item in data["items"]])
        if not request_msg.HasField("vector_clock"):
            request_msg.vector_clock.CopyFrom(suggestions.VectorClock())
        for key, value in vc.items():
            request_msg.vector_clock.clock[key] = value
        response = stub.suggest(request_msg)
    return response.suggestions, dict(response.vector_clock.clock)


LEADER_KEY = "order_executor_leader"
LEADER_TTL = 10  # seconds
RENEW_INTERVAL = 5  # seconds

host_id = socket.gethostname()
r = redis.Redis(host='redis', port=6379, decode_responses=True)


def try_become_leader():
    return r.set(LEADER_KEY, host_id, nx=True, ex=LEADER_TTL)


def renew_leadership():
    current = r.get(LEADER_KEY)
    if current == host_id:
        r.expire(LEADER_KEY, LEADER_TTL)
        return True
    return False


def is_leader():
    return r.get(LEADER_KEY) == host_id


def leader_loop():
    while True:
        if try_become_leader():
            print(f"[{host_id}] Became leader")
        elif is_leader():
            renew_leadership()
        else:
            print(f"[{host_id}] Not leader")
            time.sleep(RENEW_INTERVAL)
            continue

        item = r.lpop("order_queue")
        if item:
            process_order(item)
        time.sleep(1)


def process_order(order_json):
    order = json.loads(order_json)
    data = order["data"]
    vc = order["vector_clock"]
    order_id = data["orderId"]

    with ThreadPoolExecutor() as executor:
        f_future = executor.submit(detect_fraud, data, vc.copy())
        v_future = executor.submit(verify_transaction, data, vc.copy())
        s_future = executor.submit(suggest_books, data, vc.copy())

        fraud, vc1 = f_future.result()
        if fraud == "True":
            r.set(f"result:{order_id}", json.dumps({
                "status": "rejected",
                "suggestedBooks": []
            }), ex=30)
            print(f"[{order_id}] ❌ Fraud detected")
            return

        verify, vc2 = v_future.result()
        if verify != "False":
            r.set(f"result:{order_id}", json.dumps({
                "status": "rejected",
                "suggestedBooks": []
            }), ex=30)
            print(f"[{order_id}] ❌ Transaction failed")
            return

        suggestions, vc3 = s_future.result()
        final_vc = merge_vector_clocks(vc, vc1, vc2, vc3)

        books = []
        for i, suggestion in enumerate(suggestions.split(",")):
            if "by" in suggestion:
                title, author = suggestion.split("by")
                books.append({
                    "id": i + 1,
                    "title": title.strip(),
                    "author": author.strip()
                })

        r.set(f"result:{order_id}", json.dumps({
            "status": "approved",
            "suggestedBooks": books
        }), ex=30)

        print(
            f"[{order_id}] ✅ Order processed | Suggestions: {books} | VC: {final_vc}")


if __name__ == "__main__":
    time.sleep(5)  # Give Redis time to start
    print(f"[{host_id}] Starting leader election")
    leader_loop()
