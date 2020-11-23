#putting the packets back in to order
import socket, argparse, random, binascii, time, _thread
from random import randint
from struct import *
#from btcp import *

class Order:

    def __init__(self, filename, window_size):
        open(filename, "wb").close()
        self.file = open(filename, "ab")
        self.window = window_size
        self.acked_syn = [{}]
        self.seen = [0]*65536
        self.order = [[]]
        #self.tempw = open('temp', "w")

    def close(self):
        self.file.close()

    def write_partial(self, file, packets):
        #print("FIRST")
        #print([num for (num,data) in packets[:100]])
        packets = self.sort_packets(packets)
        #print("SECOND")
        #print([num for (num,data) in packets[:150]])
        i=0
        while i<len(packets):
            #start = int(round(time.time() * 1000))
            string = b''
            #b = 0
            for j in range(i,min(i+20,len(packets))):
                #b+=1
                (num, data) = packets[j]
                print("Printing num: ", num, " ", data[:100])
                string += data
            #add = int(round(time.time() * 1000))
            file.write(string)
            #end = int(round(time.time() * 1000))
            i+=20
            #print(str(b)+" " + str(num) + " add: " + str(add-start) + " " + "write: " + str(end-add) + " " + str(i))

    def write_all(self):
        for wrap in self.order:
            self.write_partial(self.file, wrap)
        self.file.close()

    def add_packet(self, stream_id, syn_number, content, packet):
        a = self.seen[syn_number]
        if a > 3:
            if len(self.acked_syn[0])==65536:
                print("starting thread for write")
                self.lower_count()
                _thread.start_new_thread (self.write_partial, (self.file, self.order[0]) )
                a-=1
                del self.order[0]
                del self.acked_syn[0]
        if len(self.acked_syn) <= a:
            self.acked_syn.append({})
            self.order.append([])
        self.acked_syn[a][(packet)] = True
        self.order[a].append((syn_number,content))
        self.seen[syn_number]+=1

    #This has potential failure if not all packets have been recieved once or more.
    #But this is unlikely because we check if first row is full.
    def lower_count(self):
        for i in range(len(self.seen)):
            if self.seen[i] > 0:
                self.seen[i]-=1
            else:
                print("\nError!\n")

    def recieved(self, data):
        for dict in self.acked_syn:
            if data in dict:
                return True
        return False

    #def sort_packets(self,list):
    #    #print("amount of arrays created: " + str(len(self.acked_syn)))
    #    return list.sort(key = self.sortSyn)

    def sortSyn(self, val):
        return val[0]

    def sort_packets(self, list):
        return sorted([(syn,data) for (syn,data) in list if syn >= 0], key = self.sortSyn) + sorted([(syn,data) for (syn,data) in list if syn < 0], key = self.sortSyn)

    def check_window(self):
        for i in range(len(self.order)):
            if self.order[i][0]!=1+i:
                return False
        self.write_to_file()
        return True
