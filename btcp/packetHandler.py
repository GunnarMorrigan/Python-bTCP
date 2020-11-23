import socket, argparse, random, select
from random import randint
from struct import *
from btcp import *



def receive(sock, timeout):
     a, b, c = select.select([sock], [], [], timeout/1000)
     return sock.recvfrom(1016) if a else (None, (None, None))

def handle(sock, seq, timeout, randsyn):
    for i in range(10):
        data, (source_ip, source_port) = receive(sock,timeout/10)
        if not data==None:
            (stream_id, syn_number, ack_number, syn, ack, fin, window_size, data_length, content) = decode_packet(data)
            print("received syn "+ str(syn_number) + " ack " + str(ack_number), syn, ack, fin, content[:20])
            if fin:
                closing_handshake(seq, sock, source_ip, source_port)
            elif (syn and ack):
                seq.resend_unsafe(randsyn+1,syn_number, 0, 1, 0, 3, b'ack')
            elif ack:
                seq.delete_packet(ack_number)
