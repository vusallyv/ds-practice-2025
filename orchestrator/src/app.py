import threading
import json
import uuid
from flask_cors import CORS
from flask import Flask, request
import sys
import os

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb'))
sys.path.insert(0, grpc_path)
import common_pb2 as common  # noqa
import fraud_detection_pb2 as fraud_detection  # noqa
import fraud_detection_pb2_grpc as fraud_detection_grpc  # noqa
import transaction_verification_pb2 as transaction_verification  # noqa
import transaction_verification_pb2_grpc as transaction_verification_grpc  # noqa
import suggestions_pb2 as suggestions  # noqa
import suggestions_pb2_grpc as suggestions_grpc  # noqa
import order_queue_pb2 as order_queue  # noqa
import order_queue_pb2_grpc as order_queue_grpc  # noqa
import books_database_pb2 as books_database  # noqa
import books_database_pb2_grpc as books_database_grpc  # noqa

import grpc  # noqa
from google.protobuf.json_format import MessageToDict  # noqa


def check_fraud(order_id) -> fraud_detection.OrderResponse:
    # Establish a connection with the fraud-detection gRPC service.
    with grpc.insecure_channel('fraud_detection:50051') as channel:
        # Create a stub object.
        stub = fraud_detection_grpc.FraudServiceStub(channel)
        # Call the service through the stub object.
        vector_clock = common.VectorClock(clocks=[0, 0, 0])
        request = common.Request(order_id=order_id, vector_clock=vector_clock)
        response = stub.SayFraud(request)
    return response


def initTransaction(order_id, request_data):
    with grpc.insecure_channel('transaction_verification:50051') as channel:
        # Create a stub object.
        stub = transaction_verification_grpc.VerificationServiceStub(channel)
        # Call the service through the stub object.
        billing_address = request_data['billingAddress']
        billing_address = f"{billing_address['street']}, {billing_address['zip']}, {billing_address['city']}, {billing_address['state']}, {billing_address['country']}"
        request = transaction_verification.TransactionRequest(
            name=request_data['user']['name'],
            contact=request_data['user']['contact'],
            credit_card_number=request_data['creditCard']['number'],
            expiration_date=request_data['creditCard']['expirationDate'],
            cvv=int(request_data['creditCard']['cvv']),
            billing_address=billing_address,
            quantity=sum(item['quantity'] for item in request_data['items']),
            items=request_data.get('items', [])
        )
        request = transaction_verification.InitRequest(
            order_id=order_id, transaction_request=request)
        response = stub.initVerification(request)
    return response


def initFraudVerification(order_id, request_data):
    with grpc.insecure_channel('fraud_detection:50051') as channel:
        # Create a stub object.
        stub = fraud_detection_grpc.FraudServiceStub(channel)
        # Call the service through the stub object.
        request = common.ItemsInitRequest(
            order_id=order_id, items=request_data.get('items', []))
        response = stub.InitVerification(request)
    return response


def get_suggestion(order_id) -> suggestions.Suggestions:
    with grpc.insecure_channel('suggestions:50051') as channel:
        # Create a stub object.
        stub = suggestions_grpc.SuggestionServiceStub(channel)
        # Call the service through the stub object.
        vector_clock = common.VectorClock(clocks=[0, 0, 0])
        request = common.Request(order_id=order_id, vector_clock=vector_clock)
        response = stub.SaySuggest(request)
    return response


def init_suggestion(order_id, request_data):
    with grpc.insecure_channel('suggestions:50051') as channel:
        # Create a stub object.
        stub = suggestions_grpc.SuggestionServiceStub(channel)
        # Call the service through the stub object.
        request = common.ItemsInitRequest(
            order_id=order_id, items=request_data.get('items', []))
        response = stub.initSuggestion(request)
    return response


# Import Flask.
# Flask is a web framework for Python.
# It allows you to build a web application quickly.
# For more information, see https://flask.palletsprojects.com/en/latest/

# Create a simple Flask app.
app = Flask(__name__)
# Disable sorting of keys in JSON responses
app.json.sort_keys = False
# Enable CORS for the app.
CORS(app, resources={r'/*': {'origins': '*'}})

vectorClocks = dict()  # order_id -> vector_clock


def comibine_vector_clock(order_id, new_clock):
    vectorClocks[order_id] = [max(old, new) for old, new in zip(
        vectorClocks[order_id], new_clock.clocks)]


def event_a(
        order_id,
        transaction_stub: transaction_verification_grpc.VerificationServiceStub,
        fraud_detection_stub: fraud_detection_grpc.FraudServiceStub,
        suggestions_stub: suggestions_grpc.SuggestionServiceStub):
    resp = transaction_stub.BookListNotEmtpy(common.Request(
        order_id=order_id,
        vector_clock=common.VectorClock(clocks=vectorClocks[order_id])))
    if resp.fail:
        raise FailException(resp.message)
    comibine_vector_clock(order_id, resp.vector_clock)
    event_c(order_id, transaction_stub, fraud_detection_stub, suggestions_stub)


def event_b(
        order_id,
        transaction_stub: transaction_verification_grpc.VerificationServiceStub,
        fraud_detection_stub: fraud_detection_grpc.FraudServiceStub,
        suggestions_stub: suggestions_grpc.SuggestionServiceStub):
    resp = transaction_stub.UserDataVerification(
        common.Request(
            order_id=order_id,
            vector_clock=common.VectorClock(clocks=vectorClocks[order_id])))
    if resp.fail:
        raise FailException(resp.message)
    comibine_vector_clock(order_id, resp.vector_clock)
    event_d(order_id, fraud_detection_stub, suggestions_stub)


def event_c(
        order_id,
        transaction_stub: transaction_verification_grpc.VerificationServiceStub,
        fraud_detection_stub: fraud_detection_grpc.FraudServiceStub,
        suggestions_stub: suggestions_grpc.SuggestionServiceStub):
    resp = transaction_stub.CreditCardVerification(
        common.Request(
            order_id=order_id,
            vector_clock=common.VectorClock(clocks=vectorClocks[order_id])))
    if resp.fail:
        raise FailException(resp.message)
    comibine_vector_clock(order_id, resp.vector_clock)
    event_e(order_id, fraud_detection_stub, suggestions_stub)


def event_d(
        order_id,
        fraud_detection_stub: fraud_detection_grpc.FraudServiceStub,
        suggestions_stub: suggestions_grpc.SuggestionServiceStub):
    resp = fraud_detection_stub.CheckUserData(
        common.Request(
            order_id=order_id,
            vector_clock=common.VectorClock(clocks=vectorClocks[order_id])))
    if resp.fail:
        raise FailException(resp.message)
    comibine_vector_clock(order_id, resp.vector_clock)
    event_e(order_id, fraud_detection_stub, suggestions_stub)


def event_e(order_id,
            fraud_detection_stub: fraud_detection_grpc.FraudServiceStub,
            suggestions_stub: suggestions_grpc.SuggestionServiceStub):
    # fraud-detection service checks the credit card data for fraud.
    resp = fraud_detection_stub.CheckCreditCard(
        common.Request(
            order_id=order_id,
            vector_clock=common.VectorClock(clocks=vectorClocks[order_id])))
    if resp.fail:
        raise FailException(resp.message)
    if resp.message == "Early stop":
        return
    comibine_vector_clock(order_id, resp.vector_clock)
    event_f(order_id, suggestions_stub)


def event_f(order_id,
            suggestions_stub: suggestions_grpc.SuggestionServiceStub):
    resp = suggestions_stub.SaySuggest(common.Request(
        order_id=order_id, vector_clock=common.VectorClock(clocks=vectorClocks[order_id])))
    comibine_vector_clock(order_id, resp.vector_clock)
    raise BookException(resp.books)


class BookException(Exception):
    pass


class FailException(Exception):
    pass


def execute_order(request_data):
    order_id = uuid.uuid4().hex
    vectorClocks[order_id] = [0, 0, 0]
    with grpc.insecure_channel('fraud_detection:50051') as fraud_detection_channel:
        with grpc.insecure_channel('transaction_verification:50051') as transcation_verifiction_channel:
            with grpc.insecure_channel('suggestions:50051') as suggestions_channel:
                # Initing everything
                fraud_detection_stub = fraud_detection_grpc.FraudServiceStub(
                    fraud_detection_channel)
                transaction_verification_stub = transaction_verification_grpc.VerificationServiceStub(
                    transcation_verifiction_channel)
                suggestions_stub = suggestions_grpc.SuggestionServiceStub(
                    suggestions_channel)
                billing_address = request_data['billingAddress']
                general_request = common.InitAllInfoRequest(order_id=order_id, request=common.AllInfoRequest(
                    name=request_data['user']['name'],
                    contact=request_data['user']['contact'],
                    credit_card_number=request_data['creditCard']['number'],
                    expiration_date=request_data['creditCard']['expirationDate'],
                    cvv=int(request_data['creditCard']['cvv']),
                    billing_address=f"{billing_address['street']}, {billing_address['zip']}, {billing_address['city']}, {billing_address['state']}, {billing_address['country']}",
                    quantity=sum(item['quantity']
                                 for item in request_data['items']),
                    items=request_data.get('items', [])))
                suggestions_request = common.ItemsInitRequest(
                    order_id=order_id, items=request_data.get('items', []))
                fraud_detection_stub.InitVerification(general_request)
                transaction_verification_stub.initVerification(general_request)
                suggestions_stub.initSuggestion(suggestions_request)

                suggested_books = None
                fail_error = None

                # Wrapper around threads, that catches returned message
                def thread_wrapper(target, args):
                    try:
                        target(*args)
                    except BookException as e:  # Suggestions
                        nonlocal suggested_books
                        suggested_books = e.args[0]
                    except FailException as e:  # Some kind of an error message
                        nonlocal fail_error
                        fail_error = e

                t_a = threading.Thread(target=thread_wrapper, args=(
                    event_a, (order_id, transaction_verification_stub, fraud_detection_stub, suggestions_stub)))
                t_b = threading.Thread(target=thread_wrapper, args=(
                    event_b, (order_id, transaction_verification_stub, fraud_detection_stub, suggestions_stub)))
                t_a.start()
                t_b.start()
                t_a.join()
                t_b.join()
                if fail_error is not None:
                    return {
                        'orderId': order_id,
                        'status': f'Order Rejected: {fail_error}',
                        'suggestedBooks': []
                    }
                elif suggested_books is not None:
                    # ALL CORRECT, SO send to order queue
                    with grpc.insecure_channel('order_queue:50051') as order_queue_channel:
                        order_queue_stub = order_queue_grpc.OrderQueueServiceStub(
                            order_queue_channel)
                        items_to_send = common.ItemsInitRequest(
                            order_id=order_id, items=request_data.get('items', []))
                        order_queue_stub.Enqueue(items_to_send)
                    # Finally return books to frontend
                    return {
                        'orderId': order_id,
                        'status': 'Order Approved',
                        'suggestedBooks': [MessageToDict(book) for book in suggested_books],
                    }
                else:
                    raise AssertionError(
                        "Unexpected error occurred, threads did not terminate in an expected way")

    return {
        'orderId': order_id,
        'status': 'Order Rejected',
        'suggestedBooks': [],
    }


@app.route('/checkout', methods=['POST'])
def checkout():
    return execute_order(json.loads(request.data))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
