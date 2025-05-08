import sys
import os

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb'))
sys.path.insert(0, grpc_path)
import common_pb2 as common  # noqa
import transaction_verification_pb2 as transaction_verification  # noqa
import transaction_verification_pb2_grpc as transaction_verification_grpc  # noqa

import grpc  # noqa
from concurrent import futures  # noqa


def verify_credit_card(request: common.AllInfoRequest):
    return request.credit_card_number.strip() != "" and \
        len(request.credit_card_number) == 16 and \
        len(str(request.cvv)) == 3


def verify_billing_address(request: common.AllInfoRequest):
    return request.billing_address.strip() != ""


def verify_contact(request: common.AllInfoRequest):
    return request.contact.strip() != "" and "@" in request.contact and "." in request.contact.split('@')[1]


def verify_name(request: common.AllInfoRequest):
    return request.name.strip() != "" and len(request.name.split(' ')) == 2 and \
        all([len(name) > 0 for name in request.name.split(' ')])


class VerificationService(transaction_verification_grpc.VerificationServiceServicer):
    def __init__(self, svc_idx=2, total_svcs=3):
        self.svc_idx = svc_idx
        self.total_svcs = total_svcs
        self.orders = {}  # orderId -> {data}

    def initVerification(self, request: common.InitAllInfoRequest, context=None):
        order_id = request.order_id
        data = request.request
        self.orders[order_id] = {"data": data, "vc": [0]*self.total_svcs}
        return common.Empty()

    def merge_and_incrment(self, local_vc, incoming_vc=0):
        for i in range(self.total_svcs):
            local_vc[i] = max(local_vc[i], incoming_vc[i])
        local_vc[self.svc_idx] += 1

    def BookListNotEmtpy(self, request: common.Request, context) -> common.Response:
        order_id = request.order_id
        incoming_vc = request.vector_clock.clocks
        entry = self.orders.get(order_id)
        data = entry["data"]
        self.merge_and_incrment(entry["vc"], incoming_vc)
        if len(data.items) == 0:
            response = common.Response(
                fail=True, message="Books list is empty", vector_clock=common.VectorClock(clocks=entry["vc"]))
        else:
            response = common.Response(
                fail=False, message="", vector_clock=common.VectorClock(clocks=entry["vc"]))
        return response

    def UserDataVerification(self, request, context):
        order_id = request.order_id
        incoming_vc = request.vector_clock.clocks
        entry = self.orders.get(order_id)
        data = entry["data"]
        self.merge_and_incrment(entry["vc"], incoming_vc)
        is_correct = True
        message = "All needed data is filled in"
        if verify_contact(data) is False:
            message = "Email should be filled in"
            is_correct = False
        if verify_billing_address(data) is False:
            message = "Billing address should be all filled in"
            is_correct = False
        if verify_name(data) is False:
            message = "Buyer name should be filled in"
            is_correct = False
        response = common.Response(fail=(
            is_correct is False), message=message, vector_clock=common.VectorClock(clocks=entry["vc"]))
        return response

    def CreditCardVerification(self, request, context):
        order_id = request.order_id
        incoming_vc = request.vector_clock.clocks
        entry = self.orders.get(order_id)
        data = entry["data"]
        self.merge_and_incrment(entry["vc"], incoming_vc)
        is_correct = True
        message = "Credit card information is filled in"

        if verify_credit_card(data) is False:
            message = "Credit card information is not in correct format"
            is_correct = False

        response = common.Response(fail=(
            is_correct is False), message=message, vector_clock=common.VectorClock(clocks=entry["vc"]))
        return response


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())
    # Add HelloService
    # transaction_verification_grpc.add_HelloServiceServicer_to_server(HelloService(), server)
    transaction_verification_grpc.add_VerificationServiceServicer_to_server(
        VerificationService(), server)
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
