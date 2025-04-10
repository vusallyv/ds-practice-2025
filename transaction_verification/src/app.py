from concurrent import futures
import grpc
import sys
import os
import re
import threading

# Import the gRPC stubs.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
transaction_verification_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/transaction_verification'))
sys.path.insert(0, transaction_verification_grpc_path)
import transaction_verification_pb2_grpc as transaction_verification_grpc  # noqa: E402
import transaction_verification_pb2 as transaction_verification  # noqa: E402


def event_a(request, vc, lock):
    """
    Event a: Verify that the order contains at least one item.
    This event runs concurrently with event b.
    """
    with lock:
        vc["TV"] += 1
        current_vc = vc.copy()
    print(f"Event a vector clock: {current_vc}")
    try:
        if int(request.items_length) <= 0:
            return False, "No items in order"
    except ValueError:
        return False, "Invalid items_length"
    return True, None


def event_b(request, vc, lock):
    """
    Event b: Verify that mandatory user data (e.g., name) is provided and valid.
    This event runs concurrently with event a.
    """
    with lock:
        vc["TV"] += 1
        current_vc = vc.copy()
    print(f"Event b vector clock: {current_vc}")
    if not request.name or not re.match(r'^[a-zA-Z ]+$', request.name):
        return False, "Invalid or missing name"
    return True, None


def event_c(request, vc, lock):
    """
    Event c: Verify the credit card number and expiration date.
    This event runs after event a completes.
    """
    with lock:
        vc["TV"] += 1
        current_vc = vc.copy()
    print(f"Event c vector clock: {current_vc}")
    if not re.match(r'^\d{16}$', request.credit_card_number):
        return False, "Invalid credit card number"
    if not re.match(r'^\d{2}/\d{2}$', request.credit_card_expiration_date):
        return False, "Invalid credit card expiration date"
    return True, None


def broadcast_clear_order_data(order_id, vc):
    """
    Simulated broadcast to instruct backend services to clear cached order data.
    The final vector clock is attached to the broadcast.
    """
    print(
        f"Broadcasting clear order data for order {order_id} with final vector clock: {vc}")
    # In a full implementation, you would issue a gRPC broadcast call here.
    return True


class TransactionService(transaction_verification_grpc.TransactionServiceServicer):
    def verify(self, request, context):
        """
        Updated transaction verification method implementing the event ordering:
          - Events a and b execute concurrently.
          - Event c is triggered after event a completes.
        """
        # Retrieve order_id from the request (assumes the field is now defined)
        order_id = request.order_id if hasattr(
            request, "order_id") else "unknown_order"
        # Initialize the vector clock for this order. (Key "TV" represents this service's counter.)
        vector_clock = {"TV": 0}
        lock = threading.Lock()
        print(
            f"Initializing order {order_id} with vector clock: {vector_clock}")

        # Use a thread pool to simulate concurrent event execution.
        with futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_a = executor.submit(event_a, request, vector_clock, lock)
            future_b = executor.submit(event_b, request, vector_clock, lock)
            # Wait for event_a to complete before scheduling event_c.
            result_a, error_a = future_a.result()
            future_c = executor.submit(event_c, request, vector_clock, lock)
            result_b, error_b = future_b.result()
            result_c, error_c = future_c.result()

        # Propagate the first error encountered.
        if not result_a:
            final_error = error_a
        elif not result_b:
            final_error = error_b
        elif not result_c:
            final_error = error_c
        else:
            final_error = None

        # Create and populate the TransactionResponse.
        response = transaction_verification.TransactionResponse()
        if final_error:
            response.is_fraud = final_error
            print(f"Order {order_id} verification failed: {final_error}")
        else:
            response.is_fraud = "False"  # "False" means no fraud detected.
            print(f"Order {order_id} verification succeeded")
        print(f"Final vector clock for order {order_id}: {vector_clock}")

        # Simulate a broadcast to clear cached order data.
        broadcast_clear_order_data(order_id, vector_clock)
        return response


def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    transaction_verification_grpc.add_TransactionServiceServicer_to_server(
        TransactionService(), server)
    port = "50052"
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print("Transaction Verification server started on port", port)
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
