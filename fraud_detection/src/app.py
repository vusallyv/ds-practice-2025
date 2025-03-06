import sys
import os
import re
import google.generativeai as genai

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/fraud_detection'))
sys.path.insert(0, fraud_detection_grpc_path)
import fraud_detection_pb2 as fraud_detection  # noqa: E402
import fraud_detection_pb2_grpc as fraud_detection_grpc  # noqa: E402

import grpc  # noqa: E402
from concurrent import futures  # noqa: E402

# Create a class to define the server functions, derived from
# fraud_detection_pb2_grpc.HelloServiceServicer


class HelloService(fraud_detection_grpc.HelloServiceServicer):
    # Create an RPC function to say hello
    def SayHello(self, request, context):
        # Create a HelloResponse object
        try:
            GOOGLE_API_KEY = 'AIzaSyDobw3uI4_ioNYjNzYCK5QqZumIpbiwRcY'
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-pro")
            prompt = f"The user's name is {request.name}. Their credit card expiration date is {request.credit_card_expiration_date}. They commented: {request.user_comment}. They have {request.items_length} items in their cart."
            prompt += "Please only return boolean value for fraud detection (True/False)."
            gemini_response = model.generate_content(prompt)
            print("Response from Gemini:")
            print(gemini_response.text)
            is_fraud = str(
                re.search(r'True|False', gemini_response.text).group())
        except Exception as e:
            print("Error in generating response from Gemini.")
            print(e)
            is_fraud = "False"
        response = fraud_detection.HelloResponse()
        response.is_fraud = is_fraud
        return response


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())
    # Add HelloService
    fraud_detection_grpc.add_HelloServiceServicer_to_server(
        HelloService(), server)
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
