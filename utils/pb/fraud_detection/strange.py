import fraud_detection_pb2

# Create and populate a HelloRequest message
request = fraud_detection_pb2.HelloRequest(name="a", credit_card_number="b")
# request.name["card1"] = "1234-5678-9012-3456"
# request.name["card2"] = "9876-5432-1098-7654"

# Serialize the message to binary
binary_data = request.SerializeToString()

# Save to a file
with open("hello_request.bin", "wb") as f:
    f.write(binary_data)

print("Serialized binary data saved to hello_request.bin")

# Deserialize
with open("hello_request.bin", "rb") as f:
    binary_data = f.read()

request_deserialized = fraud_detection_pb2.HelloRequest()
request_deserialized.ParseFromString(binary_data)

print("Deserialized HelloRequest:", request_deserialized)
