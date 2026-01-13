import socket
import struct
import sys

# Protocol Constants
MAGIC_COOKIE = 0xabcddcba
MSG_OFFER = 0x02
MSG_REQUEST = 0x03
MSG_PAYLOAD = 0x04

UDP_PORT = 13122
TEAM_NAME = "Team 2"

def unpack_offer(data):
    # !IBH32s: Cookie, Type, Port, Name
    return struct.unpack('!IBH32s', data)
