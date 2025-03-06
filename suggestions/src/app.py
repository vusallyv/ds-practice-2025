from concurrent import futures
import grpc
import sys
import os
import re
import google.generativeai as genai

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
suggestions_grpc_path = os.path.abspath(
    os.path.join(FILE, '../../../utils/pb/suggestions'))
sys.path.insert(0, suggestions_grpc_path)
import suggestions_pb2_grpc as suggestions_grpc  # noqa: E402
import suggestions_pb2 as suggestions  # noqa: E402


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

# Create a class to define the server functions, derived from
# suggestions_pb2_grpc.SuggestionsServiceServicer


class SuggestionsService(suggestions_grpc.SuggestionsServiceServicer):
    # Create an RPC function to say hello
    def SaySuggestions(self, request, context):
        # Create a SuggestionsResponse object
        response = suggestions.SuggestionsResponse()
        # Set the suggestions field of the response object

        try:
            GOOGLE_API_KEY = 'AIzaSyDobw3uI4_ioNYjNzYCK5QqZumIpbiwRcY'
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-pro")
            prompt = f"User purchased {request.books.split(',')}."
            prompt += f"Please suggest some books based on the user's purchase from {BOOKS} and only return the suggestions like this:"
            prompt += "The suggestions are: Book1 by Author1, Book2 by Author2, Book3 by Author3"
            gemini_response = model.generate_content(prompt)
            print("Response from Gemini:")
            print(gemini_response.text)
            book_suggestions = re.search(r'The suggestions are:(.*)', gemini_response.text, re.DOTALL)
            book_suggestions = book_suggestions.group(1)
            print(book_suggestions)
        except Exception as e:
            print("Error in generating response from Gemini.")
            print(e)
            book_suggestions = ""
        # Print the suggestions message
        # Set the suggestions field of the response object
        response.suggestions = book_suggestions
        # Return the response object
        return response


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())
    # Add SuggestionsService
    suggestions_grpc.add_SuggestionsServiceServicer_to_server(
        SuggestionsService(), server)
    # Listen on port 50053
    port = "50053"
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print("Server started. Listening on port 50053.")
    # Keep thread alive
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
