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

def pack_request(rounds):
    # !IBB32s: Cookie, Type, Rounds, Name
    padded_name = TEAM_NAME.encode('utf-8').ljust(32, b'\0')
    return struct.pack('!IBB32s', MAGIC_COOKIE, MSG_REQUEST, rounds, padded_name)

def pack_decision(decision):
    # !IB5s: Cookie, Type, String("Hittt" or "Stand")
    return struct.pack('!IB5s', MAGIC_COOKIE, MSG_PAYLOAD, decision.encode('utf-8'))

def unpack_payload(data):
    # !IBBHB: Cookie, Type, Result, Rank, Suit
    return struct.unpack('!IBBHB', data)
