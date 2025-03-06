import transaction_verification_pb2

# Create and populate a TransactionRequest message
request = transaction_verification_pb2.TransactionRequest(name="a", credit_card_number="b")
# request.name["card1"] = "1234-5678-9012-3456"
# request.name["card2"] = "9876-5432-1098-7654"

# Serialize the message to binary
binary_data = request.SerializeToString()

# Save to a file
with open("Transaction_request.bin", "wb") as f:
    f.write(binary_data)

print("Serialized binary data saved to Transaction_request.bin")

# Deserialize
with open("Transaction_request.bin", "rb") as f:
    binary_data = f.read()

request_deserialized = transaction_verification_pb2.TransactionRequest()
request_deserialized.ParseFromString(binary_data)

print("Deserialized TransactionRequest:", request_deserialized)
