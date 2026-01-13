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

def draw_card():
    """Returns (Rank, Suit) tuple. Rank 1-13, Suit 0-3."""
    return (random.randint(1, 13), random.randint(0, 3))

def handle_client(conn, addr):
    print(f"New connection from {addr}")
    try:
        # Receives Request
        data = conn.recv(1024)
        if not data: return
        cookie, msg_type, num_rounds, team_name = unpack_request(data)
        
        if cookie != MAGIC_COOKIE or msg_type != MSG_REQUEST:
            print("Invalid packet.")
            return

        team_name_str = team_name.decode('utf-8').strip('\x00')
        print(f"Player {team_name_str} wants to play {num_rounds} rounds.")

        # Game Loop
        for round_num in range(1, num_rounds + 1):
            print(f"--- Round {round_num} ---")
            
            # Initial Deal
            player_cards = [draw_card(), draw_card()]
            dealer_cards = [draw_card(), draw_card()] # 2nd is hidden
            
            player_sum = sum(get_card_value(c[0]) for c in player_cards)
            
            # Send player's 2 cards
            conn.sendall(pack_payload(RESULT_CONTINUE, player_cards[0][0], player_cards[0][1]))
            conn.sendall(pack_payload(RESULT_CONTINUE, player_cards[1][0], player_cards[1][1]))
            
            # Send dealer's 1st card
            conn.sendall(pack_payload(RESULT_CONTINUE, dealer_cards[0][0], dealer_cards[0][1]))

            # Player Turn
            busted = False
            while True:
                # Receive decision
                packet = conn.recv(1024) # Expecting Header + 5 chrs
                if len(packet) < 10: break # check
                
                # Unpack: !IB5s (Cookie, Type, "Hittt" or "Stand")
                try:
                    p_cookie, p_type, decision = struct.unpack('!IB5s', packet[:10])
                except:
                    break
                    
                cmd = decision.decode('utf-8')

                if "Hit" in cmd:
                    new_card = draw_card()
                    player_sum += get_card_value(new_card[0])
                    # Checks bust
                    if player_sum > 21:
                        # Send Card + LOSS
                        conn.sendall(pack_payload(RESULT_LOSS, new_card[0], new_card[1]))
                        busted = True
                        break
                    else:
                        # Send Card + CONTINUE
                        conn.sendall(pack_payload(RESULT_CONTINUE, new_card[0], new_card[1]))
                
                elif "Stand" in cmd:
                    break

            # Dealer Turn if player not bust
            if not busted:
                dealer_sum = sum(get_card_value(c[0]) for c in dealer_cards)
                
                # Reveal Dealer's hidden card (send it to client)
                conn.sendall(pack_payload(RESULT_CONTINUE, dealer_cards[1][0], dealer_cards[1][1]))

                while dealer_sum < 17:
                    new_card = draw_card()
                    dealer_sum += get_card_value(new_card[0])
                    # Send dealer's draw to client
                    conn.sendall(pack_payload(RESULT_CONTINUE, new_card[0], new_card[1]))

                # Determines Winner
                result = RESULT_TIE
                if dealer_sum > 21:
                    result = RESULT_WIN # Dealer busted
                elif player_sum > dealer_sum:
                    result = RESULT_WIN
                elif player_sum < dealer_sum:
                    result = RESULT_LOSS
                
                # Send Final Result (using dummy card 0,0)
                conn.sendall(pack_payload(result, 0, 0))

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()

def broadcast_offers(tcp_port):
    """Broadcasts UDP offers every 1 second."""
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    packet = pack_offer(tcp_port)
    
    print(f"Server started, listening on IP address {socket.gethostbyname(socket.gethostname())}")
    
    while True:
        try:
            udp_sock.sendto(packet, ('<broadcast>', UDP_PORT))
            time.sleep(1)
        except:
            time.sleep(1)

def start_server():
    # TCP Socket
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind(('', 0)) # Bind to any available port
    tcp_sock.listen()
    
    tcp_port = tcp_sock.getsockname()[1]
    
    # Start UDP Broadcast thread
    t = threading.Thread(target=broadcast_offers, args=(tcp_port,), daemon=True)
    t.start()
    
    while True:
        conn, addr = tcp_sock.accept()
        t_client = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t_client.start()

if __name__ == "__main__":
    start_server()
