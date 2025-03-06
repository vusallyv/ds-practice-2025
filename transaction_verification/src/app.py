from concurrent import futures
import grpc
import sys
import os

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
transaction_verification_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/transaction_verification'))
sys.path.insert(0, transaction_verification_grpc_path)
import transaction_verification_pb2_grpc as transaction_verification_grpc  # noqa: E402
import transaction_verification_pb2 as transaction_verification  # noqa: E402


# Create a class to define the server functions, derived from
# transaction_verification_pb2_grpc.TransactionServiceServicer

class TransactionService(transaction_verification_grpc.TransactionServiceServicer):
    # Create an RPC function to say hello
    def SayTransaction(self, request, context):
        # Create a TransactionResponse object
        response = transaction_verification.TransactionResponse()

        import re
        # check if the credit card number is valid
        if not re.match(r'^\d{16}$', request.credit_card_number):
            is_fraud = "Invalid credit card number"
        # check if the credit card expiration date is valid
        elif not re.match(r'^\d{2}/\d{2}$', request.credit_card_expiration_date):
            is_fraud = "Invalid credit card expiration date"
        # check if the user's name is valid
        elif not re.match(r'^[a-zA-Z ]+$', request.name):
            is_fraud = "Invalid name"
        # check if the number of items is valid
        elif not re.match(r'^\d+$', request.items_length):
            is_fraud = "Invalid number of items"
        else:
            is_fraud = "False"

        response.is_fraud = is_fraud
        # Set the is_fraud field of the response object
        print("Response from Transaction Verification:")
        print(response.is_fraud)
        # Return the response object
        return response


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())
    # Add TransactionService
    transaction_verification_grpc.add_TransactionServiceServicer_to_server(
        TransactionService(), server)
    # Listen on port 50052
    port = "50052"
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print("Server started. Listening on port 50052.")
    # Keep thread alive
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
