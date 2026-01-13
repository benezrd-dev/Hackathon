import socket
import struct
import threading
import time
import random

# Protocol Constants
MAGIC_COOKIE = 0xabcddcba
MSG_OFFER = 0x02
MSG_REQUEST = 0x03
MSG_PAYLOAD = 0x04

# Result codes
RESULT_CONTINUE = 0x0
RESULT_TIE = 0x1
RESULT_LOSS = 0x2
RESULT_WIN = 0x3

# Network Config
UDP_PORT = 13122
SERVER_NAME = "Team 1"

def pack_offer(tcp_port):
    """Packs the UDP Offer message."""
    # ! = Network Endian, I=4B, B=1B, H=2B, 32s=32B string
    padded_name = SERVER_NAME.encode('utf-8').ljust(32, b'\0')
    return struct.pack('!IBH32s', MAGIC_COOKIE, MSG_OFFER, tcp_port, padded_name)

def pack_payload(result, rank, suit):
    """Packs the TCP Payload message (Server -> Client)."""
    # I=Cookie, B=Type, B=Result, H=Rank, B=Suit
    return struct.pack('!IBBHB', MAGIC_COOKIE, MSG_PAYLOAD, result, rank, suit)

def unpack_request(data):
    """Unpacks the TCP Request message."""
    # I=Cookie, B=Type, B=Rounds, 32s=Name
    return struct.unpack('!IBB32s', data)

def get_card_value(rank):
    """Maps card rank to blackjack value."""
    if rank == 1: return 11 # Ace
    if rank >= 10: return 10 # Face cards
    return rank
