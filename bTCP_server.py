#!/usr/local/bin/python3
import socket, argparse, time
from struct import *
from btcp import *
import filecmp

#Handle arguments
parser = argparse.ArgumentParser()
parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
parser.add_argument("-o","--output", help="Where to store file", default="tmp.file")
args = parser.parse_args()

args = vars(args)
filename = args['output']
delay = args['timeout']
window = args['window']

server_ip = "127.0.0.1"
server_port = 9001

order = Order(filename, window)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((server_ip, server_port))

#while True:

#Needed for ip and port
data, (source_ip, source_port) = sock.recvfrom(1016)
dec = decode_packet(data)
OGsyn = dec[1]
stream_id = dec[0]

print("OGsyn ",OGsyn)
randsyn = randint(0,0xFFFF)

seq = Seq(stream_id, window_size=window, timeout=delay, dest_ip=source_ip, dest_port=source_port, socket=sock, randsyn=randsyn)
opening_handshake(sock, seq, data, delay)

number = 0
old = 0
loop = True

while loop:
    data, (source_ip, source_port) = receive(sock, delay)
    if data:
        number= number + 1

        if not order.recieved(data):
            dec = decode_packet(data)
            if dec:
                (stream_id, syn_number, ack_number, syn, ack, fin, window_size, data_length, content) = dec
                print("received syn "+ str(syn_number) + " ack " + str(ack_number), syn, ack, fin, content[:20])
                if fin:
                    print("Closing shake started")
                    closing_handshake(seq, sock, delay, syn_number)
                    order.write_all()
                    order.close()
                    loop = False
                elif not (ack or fin or syn):
                        order.add_packet(stream_id,syn_number-OGsyn-2,content, data)
                        seq.send_unsafe(syn_number, 0, 1, 0, 0, b'')
        else:
            old+=1
            seq.send_unsafe(int.from_bytes(data[4:6], 'little'), 0, 1, 0, 0, b'')
sock.close()
print("Recieved ", number, " packets and old: ", old)


if not filecmp.cmp(filename,"test/s.txt"):
    print("Files are not the same")
else:
    print("Files are the same")
