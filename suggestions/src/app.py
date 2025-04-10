from concurrent import futures
import grpc
import sys
import os
import re
import google.generativeai as genai

# Set up the path for the gRPC stubs.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
suggestions_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/suggestions'))
sys.path.insert(0, suggestions_grpc_path)
import suggestions_pb2_grpc as suggestions_grpc  # noqa: E402
import suggestions_pb2 as suggestions  # noqa: E402

# Global list of available books.
BOOKS = [
    {"title": "1984", "author": "George Orwell", "book_id": 1},
    {"title": "Animal Farm", "author": "George Orwell", "book_id": 2},
    {"title": "Brave New World", "author": "Aldous Huxley", "book_id": 3},
    {"title": "Fahrenheit 451", "author": "Ray Bradbury", "book_id": 4},
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger", "book_id": 5},
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "book_id": 6},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee", "book_id": 7},
    {"title": "The Lord of the Rings", "author": "J.R.R. Tolkien", "book_id": 8},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien", "book_id": 9},
    {"title": "The Da Vinci Code", "author": "Dan Brown", "book_id": 10},
    {"title": "The Alchemist", "author": "Paulo Coelho", "book_id": 11},
    {"title": "The Little Prince", "author": "Antoine de Saint-Exupéry", "book_id": 12},
]


class SuggestionsService(suggestions_grpc.SuggestionsServiceServicer):
    def suggest(self, request, context):
        # Retrieve the order ID.
        order_id = request.order_id if hasattr(
            request, "order_id") else "unknown_order"
        print(f"Suggestions service processing order: {order_id}")

        # Retrieve and update the vector clock.
        # Instead of iterating over the VectorClock object, iterate over its 'clock' field.
        vc = dict(request.vector_clock.clock)
        vc["SUG"] = vc.get("SUG", 0) + 1
        print(f"Updated vector clock in Suggestions service: {vc}")

        # Generate suggestions using Google Generative AI.
        try:
            GOOGLE_API_KEY = 'AIzaSyDobw3uI4_ioNYjNzYCK5QqZumIpbiwRcY'
            genai.configure(api_key=GOOGLE_API_KEY)
            purchased_books = request.books.split(',')
            prompt = (
                f"User purchased {purchased_books}. Based on this purchase and our available books: {BOOKS}, "
                "please suggest three books in the format: 'Book1 by Author1, Book2 by Author2, Book3 by Author3'."
            )
            gemini_response = genai.GenerativeModel(
                "gemini-1.5-pro").generate_content(prompt)
            print("Response from Gemini:")
            print(gemini_response.text)
            match = re.search(r'The suggestions are:(.*)',
                              gemini_response.text, re.DOTALL)
            if match:
                book_suggestions = match.group(1).strip()
            else:
                book_suggestions = ""
        except Exception as e:
            print("Error in generating response from Gemini.")
            print(e)
            book_suggestions = ""

        # Create and populate the SuggestionsResponse.
        response = suggestions.SuggestionsResponse()
        response.suggestions = book_suggestions
        # Update the inner 'clock' field of the vector clock in the response.
        for key, value in vc.items():
            response.vector_clock.clock[key] = value
        return response


def serve():
    # Create a gRPC server.
    server = grpc.server(futures.ThreadPoolExecutor())
    suggestions_grpc.add_SuggestionsServiceServicer_to_server(
        SuggestionsService(), server)
    # Listen on port 50053.
    port = "50053"
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Suggestions service started. Listening on port 50053.")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
