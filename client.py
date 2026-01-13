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

def play_game():
    print("Client started, listening for offer requests...")
    
    # Listens for UDP Offer
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp_sock.bind(('', UDP_PORT))
    
    data, addr = udp_sock.recvfrom(1024)
    cookie, msg_type, server_port, server_name = unpack_offer(data)
    
    if cookie != MAGIC_COOKIE or msg_type != MSG_OFFER:
        return

    server_ip = addr[0]
    server_name_str = server_name.decode('utf-8').strip('\x00')
    print(f"Received offer from {server_ip} ('{server_name_str}')")
    
    # 2. Connects with TCP
    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((server_ip, server_port))
        
        # Sends Request
        rounds = int(input("How many rounds do you want to play? "))
        tcp_sock.sendall(pack_request(rounds))
        
        # Game Loop
        # State tracking
        my_turn = True 
        
        while True:
            # Waits for packet
            packet = tcp_sock.recv(9)
            if not packet: break
            
            cookie, msg_type, result, rank, suit = unpack_payload(packet)
            
            if msg_type != MSG_PAYLOAD: continue

            # Map suit/rank for display
            suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
            
            # The logic is if Result is final, end round. If not, print card.
            if result != 0:
                print(f"Server sent result: {result} (3=Win, 2=Loss, 1=Tie)")
                if result == 3: print("You Won!")
                elif result == 2: print("You Lost!")
                else: print("It's a Tie!")
                
                my_turn = True
                continue

            # It's a card/update
            print(f"Card dealt: Rank {rank} of {suits[suit]}")
            
            if my_turn:
                move = input("Action (Hit/Stand): ").strip()
                if move.lower() == "hit":
                    tcp_sock.sendall(pack_decision("Hittt"))
                else:
                    tcp_sock.sendall(pack_decision("Stand"))
                    my_turn = False # passed turn to dealer

    except Exception as e:
        print(f"Error: {e}")
    finally:
        tcp_sock.close()
        print("Connection closed.")

if __name__ == "__main__":
    play_game()
