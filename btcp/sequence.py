#keeping track of the sequence of packets.
import socket, argparse, random, binascii, time, math
from random import randint
from struct import *
from btcp import *

class Seq:

    def __init__(self, stream_id, window_size, timeout, dest_ip, dest_port, socket, randsyn):
        self.window = window_size
        self.window_own = window_size
        self.packets = []
        self.outtime = timeout
        #syn number offset (starting syn of the other side).
        self.stream_id = stream_id
        #starting syn number
        self.randsyn = randsyn
        self.packet_num = 0
        self.acked = -1
        self.ip = dest_ip
        self.port = dest_port
        self.socket = socket
        self.EOF = False


    def reset_num(self):
        self.packet_num = 0

    """
    Checks if all packets have been acked
    """
    def finished(self, total_packets):
        return self.acked==total_packets

    """
    Wraps the syn number when the max number has been reached.
    Needed because python ints do not overflow
    """
    def syn_wrap(self):
        if self.packet_num+self.randsyn==65536:
            self.packet_num = 0

    def add_packetWT(self, time, syn_number, packet):
        self.packets.append((time, syn_number, packet))

    """
    Adjusts window size to the appropriate size
    """
    def adjust_window(self, window):
        self.window_size=window

    """
    --DEBUG--Returns packet size
    """
    def size(self):
        if len(self.packets)>self.window:
            print(len(self.packets))

    """
    --DEBUG--Prints the packet on index index
    """
    def print_packet(self,index):
        print("packet: "+ str(index))
        print(self.packets[index])

    """
    --DEBUG--Prints all packets that are in the buffer
    """
    def print_packets(self):
        print("\n\n")
        print("ALL PACKETS:\n")
        for (timestamp,syn_number,packet) in self.packets:
            print("C packet " + str(syn_number) + "was sent at " + str(timestamp))

    """
    Attempt to create new packet(s) and add them to the packet list
    """
    def create_packets(self, reader):
        if not self.EOF:
            while len(self.packets) < self.window:
                self.syn_wrap()
                content = reader.get_content()
                if content is not None:
                    (length,data) = content
                    packet = encode_packet(self.stream_id,self.packet_num+self.randsyn,window_size=self.window, data_length=length, content=data)
                    self.packets.append((None,self.packet_num+self.randsyn,packet))
                    self.packet_num+=1
                else:
                    self.EOF = True
                    break

    """
    Resents timed out packets and sents not yet sent packets
    """
    def check_packets(self):
        for i in range(min(self.window,len(self.packets))):
                (timestamp,syn_number,packet) = self.packets[i]
                if timestamp is None:
                    timestamp = int(round(time.time() * 1000))+self.outtime
                    self.socket.sendto(packet, (self.ip, self.port))
                    self.packets[i] = (timestamp,syn_number,packet)
                    #print("sent " + str(i) + " " + str(syn_number) +" "+ str(timestamp))
                elif timestamp<int(round(time.time() * 1000)):
                    timestamp = int(round(time.time() * 1000))+self.outtime
                    self.socket.sendto(packet, (self.ip, self.port))
                    self.packets[i] = (timestamp,syn_number,packet)
                    (stream_id, syn_number, ack_number, syn, ack, fin, window_size, data_length, content) = decode_packet(packet)
                    #print("resent " + str(i) + " " + str(syn_number) +" "+ str(timestamp))
    """
    Deletes a packet from packets list and increases ack counter
    """
    def delete_packet(self, syn_number):
        for i in range(len(self.packets)):
            if self.packets[i] is not None:
                (_, syn, _) = self.packets[i]
                if syn == syn_number:
                    self.packets.pop(i)
                    self.acked+=1
                    #print("C acked:" + "syn " + str(syn) + " acked:" + str(self.acked))
                    break

    """
    Old unused function
    """
    def send_packet(self, syn_number, packet):
        self.socket.sendto(packet, (self.ip, self.port))
        self.add_packetWT(int(round(time.time() * 1000))+self.outtime, syn_number, packet)

    """
    Gets all items needed for the sending of an uncoded packet
    Sends it such that it will be resent after the timeout period is over.
    """
    def send_safe(self, ack_number, syn, ack, fin, data_length, content):
        self.syn_wrap()
        syn_number = self.randsyn+self.packet_num
        packet = encode_packet(self.stream_id, syn_number, ack_number, syn, ack, fin, self.window_own, data_length, content)
        self.socket.sendto(packet, (self.ip, self.port))
        self.add_packetWT(int(round(time.time() * 1000))+self.outtime, syn_number, packet)
        self.packet_num+=1
        return syn_number

    """
    Gets all items needed for the sending of an uncoded packet
    Sends it such that it will not be resent after the timeout period is over.
    """
    def send_unsafe(self, ack_number, syn, ack, fin, data_length, content):
        self.syn_wrap()
        syn_number = self.randsyn+self.packet_num
        packet = encode_packet(self.stream_id, syn_number, ack_number, syn, ack, fin, self.window_own, data_length, content)
        self.socket.sendto(packet, (self.ip, self.port))
        self.packet_num+=1
        return syn_number


    """
    Gets all items needed for the sending of an uncoded packet
    Sends it such that it will not be resent after the timeout period is over.
    """
    def resend_unsafe(self, syn_number, ack_number, syn, ack, fin, data_length, content):
        packet = encode_packet(self.stream_id, syn_number, ack_number, syn, ack, fin, self.window_own, data_length, content)
        self.socket.sendto(packet, (self.ip, self.port))
        return syn_number
