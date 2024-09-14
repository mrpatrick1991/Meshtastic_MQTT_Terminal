from meshtastic import mesh_pb2, mqtt_pb2, portnums_pb2, telemetry_pb2
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from google.protobuf.json_format import MessageToDict
import paho.mqtt.client as mqtt
import base64
import random
import argparse
import json
import sys 

default_mqtt_url = "mqtt.meshtastic.org"
default_mqtt_password = "large4cats"
default_mqtt_user = "meshdev"
default_mqtt_id = "stw342df42"
default_mqtt_topic = ["msh/US/#", "msh/EU_868/#"]
default_mqtt_port = 1883
default_encryption_key = "1PG7OiApB1nwvP+rz05pAQ=="
mqtt_keepalive = 60


def decode_encrypted(message_packet):
    try:
        key_bytes = base64.b64decode(args.key.encode("ascii"))
        nonce_packet_id = getattr(message_packet, "id").to_bytes(8, "little")
        nonce_from_node = getattr(message_packet, "from").to_bytes(8, "little")
        nonce = nonce_packet_id + nonce_from_node

        cipher = Cipher(
            algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        decrypted_bytes = (
            decryptor.update(getattr(message_packet, "encrypted"))
            + decryptor.finalize()
        )

        data = mesh_pb2.Data()
        data.ParseFromString(decrypted_bytes)
        message_packet.decoded.CopyFrom(data)

        if getattr(message_packet, "from") in args.nodenums or len(args.nodenums) == 0:

            if message_packet.decoded.portnum == portnums_pb2.TEXT_MESSAGE_APP:
                payload = message_packet.decoded.payload.decode("utf-8")
                port = "TEXT_MESSAGE_APP"

            elif message_packet.decoded.portnum == portnums_pb2.NODEINFO_APP:
                pb = mesh_pb2.User()
                pb.ParseFromString(message_packet.decoded.payload)
                payload = MessageToDict(pb, preserving_proto_field_name=True)
                port = "NODEINFO_APP"

            elif message_packet.decoded.portnum == portnums_pb2.POSITION_APP:
                pb = mesh_pb2.Position()
                pb.ParseFromString(message_packet.decoded.payload)
                payload = MessageToDict(pb, preserving_proto_field_name=True)
                port = "POSITION_APP"

            elif message_packet.decoded.portnum == portnums_pb2.TELEMETRY_APP:
                pb = telemetry_pb2.Telemetry()
                pb.ParseFromString(message_packet.decoded.payload)
                payload = MessageToDict(pb, preserving_proto_field_name=True)
                port = "TELEMETRY_APP"

            elif message_packet.decoded.portnum == portnums_pb2.MAPREPORT_APP:
                pb = mqtt_pb2.MapReport()
                pb.ParseFromString(message_packet.decoded.payload)
                payload = MessageToDict(pb, preserving_proto_field_name=True)
                port = "MAPREPORT_APP"

            parsed = {
                "from": getattr(message_packet, "from"),
                "to": getattr(message_packet, "to"),
                "id": getattr(message_packet, "id"),
                "port": port,
                "data": payload,
            }

            print(json.dumps(parsed))

    except Exception as e:
        if args.verbose:
            print(f"Decryption failed: {str(e)}")


def on_connect(client, userdata, flags, rc, properties):
    if args.verbose:
        if rc == 0:
            print(f"Connected to {args.url} on {args.topic}")
        else:
            print(f"Failed to connect to MQTT broker with result code {str(rc)}")


def on_message(client, userdata, msg):
    service_envelope = mqtt_pb2.ServiceEnvelope()
    try:
        service_envelope.ParseFromString(msg.payload)
        message_packet = service_envelope.packet
        if message_packet.HasField("encrypted") and not message_packet.HasField(
            "decoded"
        ):
            decode_encrypted(message_packet)
        else:
            pass
    except Exception as e:
        if args.verbose:
            print(f"Error parsing message: {str(e)}")
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Meshtastic MQTT ETL",
        description="Connect to a meshtastic MQTT server and topic(s), then parse received packets to stdout",
    )
    parser.add_argument(
        "--url", type=str, default=default_mqtt_url, help="MQTT server URL"
    )
    parser.add_argument(
        "--port", type=int, default=default_mqtt_port, help="MQTT server port"
    )
    parser.add_argument("--user", type=str, default=default_mqtt_user, help="MQTT user")
    parser.add_argument(
        "--password", type=str, default=default_mqtt_password, help="MQTT password"
    )
    parser.add_argument(
        "--nodenums",
        nargs="*",
        type=int,
        default=[],
        help="filter to only include messages from specified node numbers",
    )
    parser.add_argument("--id", type=str, default=default_mqtt_id, help="MQTT client id")
    parser.add_argument(
        "--key",
        type=str,
        default=default_encryption_key,
        help="meshtastic encryption key",
    )
    parser.add_argument("--verbose", action="store_true", help="enable verbose output")
    parser.add_argument(
        "--topic", nargs="+", default=default_mqtt_topic, type=str, help="MQTT topic(s)"
    )

    args = parser.parse_args()
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2, client_id=args.id, clean_session=False
    )
    client.username_pw_set(username=args.user, password=args.password)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(args.url, args.port, mqtt_keepalive)
        for topic in args.topic:
            client.subscribe(topic, 0)
        client.loop_forever()
    except KeyboardInterrupt:
        client.disconnect()
        sys.exit()
