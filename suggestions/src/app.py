"""
Suggestions Service

Provides book suggestions based on users' order. It uses a similarity algorithm
to recommend books that are most relevant to the order.

Uses vector clocks to maintain consistency across services.

"""
import sys
import os

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb'))
sys.path.insert(0, grpc_path)
import common_pb2 as common  # noqa
import suggestions_pb2 as suggestions  # noqa
import suggestions_pb2_grpc as suggestions_grpc  # noqa

import grpc  # noqa
from concurrent import futures  # noqa
from pydantic import BaseModel  # noqa

from pydantic_ai import Agent  # noqa


class BookSuggestion(BaseModel):
    bookId: str
    title: str
    author: str


def findMostSimilarBooks(order):
    # request to OpenAI API to get the most similar books
    # for each book in the order, find the most similar book in the existing books
    # and return the list of most similar books

    model = os.getenv('PYDANTIC_AI_MODEL', 'openai:gpt-4o')
    agent = Agent(model, output_type=list[BookSuggestion])
    result = agent.run_sync(
        f"Find the most similar books to the following order: {order}.",
        max_tokens=1000,
        temperature=0.5,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    print("Result: " + str(result))

    try:
        # Parse the response
        similarBooks = []
        for book in result.output:
            similarBooks.append(
                suggestions.Book(bookId=book.bookId, title=book.title, author=book.author)  # noqa
            )
        return similarBooks
    except Exception as e:
        print("Error: " + str(e))
        return []


class SuggestionsService(suggestions_grpc.SuggestionServiceServicer):
    def __init__(self, svc_idx=1, total_svcs=3):
        self.svc_idx = svc_idx
        self.total_svcs = total_svcs
        self.orders = {}  # orderId -> {data}

    def initSuggestion(self, request, context=None):
        order_id = request.order_id
        data = request.items
        self.orders[order_id] = {"data": data, "vc": [0]*self.total_svcs}
        return common.Empty()

    def merge_and_incrment(self, local_vc, incoming_vc=0):
        for i in range(self.total_svcs):
            local_vc[i] = max(local_vc[i], incoming_vc[i])
        local_vc[self.svc_idx] += 1
    # Create an RPC function to say hello

    def SaySuggest(self, request, context):
        order_id = request.order_id
        incoming_vc = request.vector_clock.clocks
        entry = self.orders.get(order_id)
        self.merge_and_incrment(entry["vc"], incoming_vc)
        response = suggestions.Suggestions(
            vector_clock=common.VectorClock(clocks=entry["vc"]))
        response.books.extend(findMostSimilarBooks(entry["data"]))
        return response


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())
    # Add HelloService
    # suggestions_grpc.add_HelloServiceServicer_to_server(HelloService(), server)
    suggestions_grpc.add_SuggestionServiceServicer_to_server(
        SuggestionsService(), server)
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
