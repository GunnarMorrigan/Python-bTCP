import socket, argparse, random, binascii, os, math
from random import randint
from struct import *
from btcp import *

class Read:

    def __init__(self, filename, window_size, size):
        self.size = size
        self.file = open(filename, "rb")
        self.window = window_size
        self.syn = 0
        self.content = []
        self.create_content()

    def close(self):
        self.file.close()

    def read_content(self):
        data = self.file.read(1000)
        self.content.append( (len(data),data) )
        self.syn+=1

    def create_content(self):
        while self.syn < self.size and len(self.content)<300:
            self.read_content()

    def get_content(self):
        #print(len(self.content))
        if len(self.content) > 0:
            if(self.syn < self.size):
                self.read_content()
            return self.content.pop(0)
        else:
            return None

    def size(self):
        return self.size
