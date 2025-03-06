import json
import random
from flask_cors import CORS
from flask import Flask, request
import sys
import os


# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/fraud_detection'))
sys.path.insert(0, fraud_detection_grpc_path)
import fraud_detection_pb2 as fraud_detection  # noqa: E402
import fraud_detection_pb2_grpc as fraud_detection_grpc  # noqa: E402

transaction_verification_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/transaction_verification'))
sys.path.insert(0, transaction_verification_grpc_path)
import transaction_verification_pb2 as transaction_verification  # noqa: E402
import transaction_verification_pb2_grpc as transaction_verification_grpc  # noqa: E402


suggestions_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/suggestions'))
sys.path.insert(0, suggestions_grpc_path)
import suggestions_pb2 as suggestions  # noqa: E402
import suggestions_pb2_grpc as suggestions_grpc  # noqa: E402

import grpc  # noqa: E402


def detect_fraud(data: dict):
    # Establish a connection with the fraud-detection gRPC service.
    with grpc.insecure_channel('fraud_detection:50051') as channel:
        # Create a stub object.
        stub = fraud_detection_grpc.HelloServiceStub(channel)
        # Call the service through the stub object.
        request = fraud_detection.HelloRequest()
        # Set the request object's fields.
        request.name = data["user"]["name"]
        request.credit_card_number = data["creditCard"]["number"]
        request.credit_card_expiration_date = data["creditCard"]["expirationDate"]
        request.user_comment = data["userComment"]
        request.items_length = str(len(data["items"]))
        # Call the service through the stub object.
        response = stub.SayHello(request)
    return response.is_fraud


def verify_transaction(data: dict):
    # Establish a connection with the fraud-detection gRPC service.
    with grpc.insecure_channel('transaction_verification:50052') as channel:
        # Create a stub object.
        stub = transaction_verification_grpc.TransactionServiceStub(channel)
        # Call the service through the stub object.
        request = transaction_verification.TransactionRequest()
        # Set the request object's fields.
        request.name = data["user"]["name"]
        request.credit_card_number = data["creditCard"]["number"]
        request.credit_card_expiration_date = data["creditCard"]["expirationDate"]
        request.items_length = str(len(data["items"]))
        # Call the service through the stub object.
        response = stub.SayTransaction(request)
    return response.is_fraud


def suggest_books(data: dict):
    # Establish a connection with the fraud-detection gRPC service.
    with grpc.insecure_channel('suggestions:50053') as channel:
        # Create a stub object.
        stub = suggestions_grpc.SuggestionsServiceStub(channel)
        # Call the service through the stub object.
        request = suggestions.SuggestionsRequest()
        # Set the request object's fields.
        request.books = ','.join([item["name"] for item in data["items"]])
        # Call the service through the stub object.
        response = stub.SaySuggestions(request)
    return response.suggestions


# Import Flask.
# Flask is a web framework for Python.
# It allows you to build a web application quickly.
# For more information, see https://flask.palletsprojects.com/en/latest/
# Create a simple Flask app.
app = Flask(__name__)
# Enable CORS for the app.
CORS(app, resources={r'/*': {'origins': '*'}})

# Define a GET endpoint.


@app.route('/', methods=['GET'])
def index():
    """
    Responds with 'Hello, [name]' when a GET request is made to '/' endpoint.
    """
    # Test the fraud-detection gRPC service.
    response = detect_fraud(request={'name': 'orchestrator'})
    # Return the response.
    return response


@app.route('/checkout', methods=['POST'])
def checkout():
    """
    Responds with a JSON object containing the order ID, status, and suggested books.
    """
    # Get request object data to json
    request_data = json.loads(request.data)
    print("Detecting fraud...")
    response = detect_fraud(data=request_data)
    print("Fraud detected:", response)
    if response == "True":
        return {'error': 'Fraud detected'}

    print("Verifying transaction...")
    response = verify_transaction(data=request_data)
    print("Transaction verified:", "Failed" if response != "False" else "Success")
    if response != "False":
        return {'error': response}

    print("Suggesting books...")
    response = suggest_books(data=request_data)
    print("Books suggested:", response)
    try:
        suggested_books = [
            {"title": book.split("by")[0].strip(), "author": book.split("by")[1].strip()} for book in response.split(",")]
    except Exception:
        suggested_books = random.sample([
            {"title": "1984", "author": "George Orwell", "book_id": 1},
            {"title": "Animal Farm", "author": "George Orwell", "book_id": 2},
            {"title": "Brave New World", "author": "Aldous Huxley", "book_id": 3},
            {"title": "Fahrenheit 451", "author": "Ray Bradbury", "book_id": 4},
            {"title": "The Catcher in the Rye",
                "author": "J.D. Salinger", "book_id": 5},
            {"title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald", "book_id": 6},
            {"title": "To Kill a Mockingbird", "author": "Harper Lee", "book_id": 7},
            {"title": "The Lord of the Rings",
                "author": "J.R.R. Tolkien", "book_id": 8},
            {"title": "The Hobbit", "author": "J.R.R. Tolkien", "book_id": 9},
            {"title": "The Da Vinci Code", "author": "Dan Brown", "book_id": 10},
            {"title": "The Alchemist", "author": "Paulo Coelho", "book_id": 11},
            {"title": "The Little Prince",
                "author": "Antoine de Saint-Exupéry", "book_id": 12},
        ], 3)

    order_status_response = {
        'orderId': random.randint(10000, 99999),
        'status': 'Order Approved',
        'suggestedBooks': suggested_books
    }

    return order_status_response


if __name__ == '__main__':
    # Run the app in debug mode to enable hot reloading.
    # This is useful for development.
    # The default port is 5000.
    app.run(host='0.0.0.0')
