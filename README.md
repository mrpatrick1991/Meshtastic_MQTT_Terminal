# Meshtastic_MQTT_Terminal

This project is forked from https://github.com/Bamorph/Meshtastic_MQTT_Terminal. It provides a CLI which subscribes to a Meshtastic MQTT server and logs recevied packets to stdout after decrypting and decoding their protobuf contents. 

```options:
  -h, --help            show this help message and exit
  --url URL             MQTT server URL
  --port PORT           MQTT server port
  --user USER           MQTT user
  --password PASSWORD   MQTT password
  --nodenums [NODENUMS ...]
                        filter to only include messages from specified node
                        numbers
  --id ID               MQTT client id
  --key KEY             meshtastic encryption key
  --verbose             enable verbose output
  --topic TOPIC [TOPIC ...]
                        MQTT topic(s)
```



The default configuration subscribes to the two largest topics (`/msh/US/` and `/msh/EU_868/`) and uses the primary meshtastic encryption key, mqtt server, username and password. 
