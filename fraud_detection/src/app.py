import sys
import os

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb'))
sys.path.insert(0, grpc_path)
import common_pb2 as common  # noqa
import fraud_detection_pb2 as fraud_detection  # noqa
import fraud_detection_pb2_grpc as fraud_detection_grpc  # noqa
import re  # noqa
from datetime import datetime  # noqa

import grpc  # noqa

from pydantic import BaseModel  # noqa
from concurrent import futures  # noqa
from pydantic_ai import Agent  # noqa


class FraudDetectionResponse(BaseModel):
    is_fraud: bool
    message: str


class FraudService(fraud_detection_grpc.FraudServiceServicer):
    def __init__(self, svc_idx=0, total_svcs=3):
        self.svc_idx = svc_idx
        self.total_svcs = total_svcs
        self.orders = {}

    def InitVerification(self, request: common.InitAllInfoRequest, context=None):
        order_id = request.order_id
        data = request.request
        self.orders[order_id] = {"data": data, "vc": [0]*self.total_svcs}
        return common.Empty()

    def merge_and_incrment(self, local_vc, incoming_vc=0):
        for i in range(self.total_svcs):
            local_vc[i] = max(local_vc[i], incoming_vc[i])
        local_vc[self.svc_idx] += 1

    def CheckUserData(self, request: common.Request, context):
        order_id = request.order_id
        incoming_vc = request.vector_clock.clocks
        entry = self.orders.get(order_id)
        data = entry["data"]
        self.merge_and_incrment(entry["vc"], incoming_vc)
        fail = False
        message = ""
        items = data.items
        totalAmount = sum([item.quantity for item in items])
        if (len(items) >= 10):
            fail = True
            message = "Ordered too many different items"
        elif (totalAmount >= 10):
            fail = True
            message = "Ordered too many items total"
        else:
            valid = re.match(
                r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                data.contact)
            if valid is False:
                fail = True
                message = "Contact should be valid"

        response = common.Response(
            message=message,
            fail=fail,
            vector_clock=common.VectorClock(clocks=entry["vc"]))
        return response

    def CheckCreditCard(self, request: common.Request, context):
        order_id = request.order_id
        incoming_vc = request.vector_clock.clocks
        entry = self.orders.get(order_id)
        data = entry["data"]
        self.merge_and_incrment(entry["vc"], incoming_vc)
        if (entry["vc"][2] < 3 or entry["vc"][0] < 3):
            response = common.Response(
                message="Early stop",
                fail=False,
                vector_clock=common.VectorClock(clocks=entry["vc"]))
            return response
        fail = False
        message = "User data is OK"
        if len(str(data.cvv)) != 3:
            message = "CVV is wrong"
            fail = True
        if len(str(data.credit_card_number)) != 16:
            message = "Credit card number is wrong"
            fail = True
        month = int(data.expiration_date.split('/')[0])
        year = int(data.expiration_date.split('/')[1])
        current_month = datetime.now().month
        current_year = (datetime.now().year) % 100
        if current_year > year:
            message = "Credit card has expired"
            fail = True
        if current_year == year and current_month > month:
            message = "Credit card has expired"
            fail = True
        response = common.Response(
            message=message,
            fail=fail,
            vector_clock=common.VectorClock(clocks=entry["vc"]))
        return response

    def SayFraud(self, request: common.Request, context):
        order_id = request.order_id
        incoming_vc = request.vector_clock.clocks
        entry = self.orders[order_id]
        data = entry["data"]
        self.merge_and_incrment(entry["vc"], incoming_vc)

        response = fraud_detection.OrderResponse()
        model = os.getenv('PYDANTIC_AI_MODEL', 'openai:gpt-4o')
        agent = Agent(model, output_type=FraudDetectionResponse)
        result = agent.run_sync(
            f"Is this order a fraud? {data}.",
            max_tokens=1000,
            temperature=0.5,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        print("FraudService - Result: " + str(result))
        response.is_fraud = result.output.is_fraud
        response.message = result.output.message
        return response


def serve():
    server = grpc.server(futures.ThreadPoolExecutor())
    fraud_detection_grpc.add_FraudServiceServicer_to_server(
        FraudService(), server)
    port = "50051"
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started. Listening on port 50051.")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
