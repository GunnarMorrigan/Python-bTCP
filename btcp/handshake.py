import socket, argparse, random, binascii, time
from random import randint
from struct import *
from btcp import *
from .packetHandler import receive

def open_handshake(sock, randsyn, seq, timeout):
    seq.send_safe(0, 1, 0, 0, 9, b'THISISSYN')

    data, (source_ip, source_port) = receive(sock, timeout)
    while True:
        if data:
            (stream_id, syn_number, ack_number, syn, ack, fin, window_size, data_length, content) = decode_packet(data)
            if (syn and ack and ack_number==randsyn+1):
                seq.delete_packet(randsyn)
                seq.send_unsafe(syn_number, 0, 1, 0, 9, b'THISISACK')
                return True
        else:
            seq.check_packets()
        data, (source_ip, source_port) = receive(sock, timeout)

def opening_handshake(sock, seq, data, timeout):
    dec = decode_packet(data)
    if dec is not None:
        (a_stream_id, a_syn_number, a_ack_number, a_syn, a_ack, a_fin, a_window_size, a_data_length, a_content) = dec
        if a_syn:
            print("syn_ack sent")
            syn = seq.send_safe(a_syn_number+1, 1, 1, 0, 12, b'THISISSYNACK')
            seq.adjust_window(a_window_size)

            while True:
                data, (source_ip, source_port) = receive(sock, timeout)
                if data:
                    (stream_id, syn_number, ack_number, syn, ack, fin, window_size, data_length, content) = decode_packet(data)
                    if ack:
                        print("handshake completed")
                        return True
                else:
                    seq.check_packets()

def close_handshake(seq, sock, timeout):
    print("C closing handshake")
    syn = seq.send_safe(0, 0, 0, 1, 9, b'THISISFIN')

    fin_f = None
    ack_f = None
    ack = 0

    while not fin_f and not ack_f and not ack==syn-1:
        data, addr = receive(sock, timeout)
        while not data:
                print("Close handshake error")
                seq.check_packets()
                data, addr = receive(sock, timeout)

        (stream_id, syn_number, ack_number, syn, ack, fin, window_size, data_length, content) = decode_packet(data)
        if(fin and ack):
            syn = seq.send_unsafe(syn_number-1, 0, 1, 0, 13, b'HELLOMYFRIEND')
            return True

def closing_handshake(seq, sock, timeout, syn):
    print("S closing handshake")
    syn_number = seq.send_safe(syn-1, 0, 1, 1, 12, b'THISISFINACK')

    for i in range(100):
        data, (source_ip, source_port) = receive(sock, timeout)
        if data:
            (_, c_syn_number, ack_number, syn_f, ack_f, fin_f, _, _, _) = decode_packet(data)
            if (ack_f and not (syn_f and fin_f)) and ack_number==syn_number-1:
                print("Close completed")
                return True;
            elif(c_syn_number==syn and (fin_f and not (syn_f and ack_f))):
                syn_number = seq.send_safe(syn-1, 0, 1, 1, 12, b'THISISFINACK')
    print("CLOSE NOT GOOD")
