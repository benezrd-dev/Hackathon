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
SERVER_NAME = "Team Mystic"
