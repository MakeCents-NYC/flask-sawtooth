from sawtooth_sdk.protobuf.validator_pb2 import Message
import zmq
import uuid
from sawtooth_sdk.protobuf import client_batch_submit_pb2

def watch_batch(batch_id):
    # Setup a connection to the validator
    ctx = zmq.Context()
    socket = ctx.socket(zmq.DEALER)
    socket.connect('tcp://localhost:4004')

    # Construct the request
    request = client_batch_submit_pb2.ClientBatchStatusRequest(
        batch_ids=[batch_id], wait=True).SerializeToString()

    # Construct the message wrapper
    correlation_id = batch_id + uuid.uuid4().hex  # This must be unique for all in-process requests
    msg = Message(
        correlation_id=correlation_id,
        message_type=Message.CLIENT_BATCH_STATUS_REQUEST,
        content=request
    )

    # Send the request
    socket.send_multipart([msg.SerializeToString()])

    # Receive the response
    resp = socket.recv_multipart()[-1]

    # Parse the message wrapper
    msg = Message()
    msg.ParseFromString(resp)

    # Validate the response type
    if msg.message_type != Message.CLIENT_BATCH_STATUS_RESPONSE:
        print("Unexpected response message type")
        return

    # Parse the response
    response = client_batch_submit_pb2.ClientBatchStatusResponse()
    response.ParseFromString(msg.content)

    # Validate the response status
    if response.status != client_batch_submit_pb2.ClientBatchSubmitResponse.OK:
        print("watch batch status failed: {}".format(response.response_message))
        return

    # Close the connection to the validator
    socket.close()

    return client_batch_submit_pb2.ClientBatchStatus.Status.Name(response.batch_statuses[0].status)


print(watch_batch('23d44854d471683873525cfeeaacd729d37e1bcc816fc001a18f39af838b82b7754d4f41a5f1fb9517e12f10084afed5b4c7d93cd24a4ef129e08248f3137059'))