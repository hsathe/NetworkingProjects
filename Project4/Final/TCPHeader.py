import socket
from struct import *
from client import *

# Class to construct a TCP Header
class TCPHeader:
    # Constuctor to initialize header values
   def __init__(self):

       self.sourcePort = 0
       self.destPort = 0
       self.sequenceNo = 530
       self.ackNo = 0
       self.HL_Offset = 5
       self.reserved_bits = 0
       self.urg_flg = 0
       self.ack_flg = 0
       self.psh_flg = 0
       self.rst_flg = 0
       self.syn_flg = 0
       self.fin_flg = 0
       self.adv_window_size = socket.htons(58400)
       self.TCP_checksum = 0
       self.urg_ptr = 0
       self.data = ""

    # Sets the required values in the TCP header
   def setValues(self, sourcePort, destPort, sequenceNo, ackNo, syn_flag, ack_flag, fin_flag, data):
       self.sourcePort = sourcePort
       self.destPort = destPort
       self.sequenceNo = sequenceNo
       self.ackNo = ackNo
       self.ack_flg = ack_flag
       self.syn_flg = syn_flag
       self.fin_flg = fin_flag
       #self.adv_window_size = socket.htons(58400)
       self.data = data

    # Builds the TCP Packet and returns TCP header
   def build(self, sourceIP, destinationIP):
       self.HL_Offset = (self.HL_Offset << 4) + 0

       flags = self.fin_flg + \
               (self.syn_flg << 1) + \
               (self.rst_flg << 2) + \
               (self.psh_flg << 3) + \
               (self.ack_flg << 4) + \
               (self.urg_flg << 5)
        # Builds TCP header
       TCP_header = pack("!HHLLBBHHH", self.sourcePort, self.destPort, self.sequenceNo, self.ackNo, self.HL_Offset, flags, self.adv_window_size, self.TCP_checksum, self.urg_ptr)

       reserved_bits = 0
       length = len(TCP_header) + len(self.data)
       pseudo_TCPHeader = pack('!4s4sBBH', socket.inet_aton(sourceIP), socket.inet_aton(destinationIP), reserved_bits, socket.IPPROTO_TCP, length)
       pseudo_TCPHeader = pseudo_TCPHeader + TCP_header + self.data

       r = RawSocket()
       self.TCP_checksum = r.calculateCheckSum(pseudo_TCPHeader)

       TCP_header = pack("!HHLLBBH", self.sourcePort, self.destPort, self.sequenceNo, self.ackNo, self.HL_Offset, flags, self.adv_window_size) + pack('H', self.TCP_checksum) + pack("!H", self.urg_ptr)
       return TCP_header

    # Extracts the TCP header data into variables
   def extract(self, data):
       tcp_header = unpack('!HHLLBBHHH' , data)

       self.sourcePort = tcp_header[0]
       #print "source port in TCP " + str(self.sourcePort)
       self.destPort = tcp_header[1]
       #print "dest port in TCP " + str(self.destPort)
       self.sequenceNo = tcp_header[2]
       self.ackNo = tcp_header[3]
       hl_offset = tcp_header[4]
       get_reserved_flags = tcp_header[5]

       self.HL_Offset = hl_offset >> 4
       self.reserved_bits = ((hl_offset & 0xF) << 2) + (get_reserved_flags >> 6)

       flags = get_reserved_flags & 0x3F
       self.urg_flg = (flags & 0x20) >> 5
       self.ack_flg = (flags & 0x10) >> 4
       self.psh_flg = (flags & 0x08) >> 3
       self.rst_flg = (flags & 0x04) >> 2
       self.syn_flg = (flags & 0x02) >> 1
       self.fin_flg = flags & 0x01

       self.adv_window_size = tcp_header[6]
       self.TCP_checksum = tcp_header[7]
       self.urg_ptr = tcp_header[8]