#!/usr/local/bin/python3
import socket, argparse, random, binascii, os
from random import randint
from struct import *
from btcp import *

#Handle arguments
parser = argparse.ArgumentParser()
parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
parser.add_argument("-i","--input", help="File to send", default="tmp.file")
args = parser.parse_args()

args = vars(args)
filename = args['input'] # opening for [r]eading as [b]inary
window = args['window']
delay = args['timeout']

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

num_packets = math.ceil(os.stat(filename).st_size/1000)
randsyn = randint(0, 0xFFFF)
print("Randsyn ",randsyn)

stream_id = randint(0, 0xffffffff)
seq = Seq(stream_id, window_size=window, timeout=delay, dest_ip=destination_ip, dest_port=destination_port, socket=sock, randsyn=randsyn)
reader = Read(filename, window, num_packets)

open_handshake(sock, randsyn, seq, delay)
seq.create_packets(reader)

print(num_packets)
while not seq.finished(num_packets):
    seq.check_packets()
    seq.size()
    handle(sock, seq, delay, randsyn)
    seq.create_packets(reader)
print("C: Started closing handshake")
reader.close()
close_handshake(seq, sock, delay)
