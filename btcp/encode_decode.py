#will become stream which will have a static stream ID to create the packets

import socket, argparse, random, binascii
from random import randint
from struct import *
from btcp import *

"""

takes in the arguments that are required to create a packet.
And then returns a fully assambled packet.

"""
def encode_packet(stream_id, syn_number, ack_number=0, SYN=0, ACK=0, FIN=0, window_size=100, data_length=0, content=b''):
    flags = SYN * 4 + ACK * 2 + FIN
    header = pack(Header_Format, stream_id, syn_number, ack_number, flags, window_size, data_length)

    payload = b''
    for i in range (data_length):
        payload += pack('B', content[i])

    checksum = pack(Checksum_Format, binascii.crc32(header + payload))
    return header + checksum + payload

def decode_packet(packet):
    (stream_id, syn_number, ack_number, flags, window_size, data_length, checksum,) = unpack(Header_Format + Checksum_Format, packet[0:16])
    header = packet[0:12]

    payload = b''

    for i in range (data_length):
        payload += pack('B', packet[i+16])

    new_checksum = binascii.crc32(header + payload)
    if checksum != new_checksum:
        return None

    (syn, ack, fin) = dec_flags(flags)
    return (stream_id, syn_number, ack_number, syn, ack, fin, window_size, data_length, payload)

def dec_flags(flags):
    syn = (flags & 4) >> 2
    ack = (flags & 2) >> 1
    fin = (flags & 1)
    return (syn, ack, fin)
