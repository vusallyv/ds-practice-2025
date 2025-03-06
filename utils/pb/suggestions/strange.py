import suggestions_pb2

# Create and populate a SuggestionsRequest message
request = suggestions_pb2.SuggestionsRequest(books="a, b")
# request.name["card1"] = "1234-5678-9012-3456"
# request.name["card2"] = "9876-5432-1098-7654"

# Serialize the message to binary
binary_data = request.SerializeToString()

# Save to a file
with open("Suggestions_request.bin", "wb") as f:
    f.write(binary_data)

print("Serialized binary data saved to Suggestions_request.bin")

# Deserialize
with open("Suggestions_request.bin", "rb") as f:
    binary_data = f.read()

request_deserialized = suggestions_pb2.SuggestionsRequest()
request_deserialized.ParseFromString(binary_data)

print("Deserialized SuggestionsRequest:", request_deserialized)
