import socket
import struct

# Class to constuct an IP header
class IPHeader:
    # Constructor to initialize all the variables
    def __init__(self, sourceIP, destinationIP, id):
        #print "in init"
        self.version = 4
        self.ihl = 5
        self.tos = 0
        self.totalLength = 0
        self.id = id
        self.flags = 0
        self.offset = 0
        self.ttl = 255
        self.protocol = socket.IPPROTO_TCP
        self.checksum = 0
        self.sourceIP = sourceIP
        self.destinationIP = destinationIP

    # Builds an IP Packet
    def build(self):
        ip_ihl_ver = (self.version << 4) + self.ihl
        word2 = (self.flags << 13) + self.offset
        ipheader = struct.pack('!BBHHHBBH4s4s', ip_ihl_ver, self.tos, self.totalLength, self.id,
                                    word2, self.ttl, self.protocol, self.checksum,
                                    socket.inet_aton(self.sourceIP), socket.inet_aton(self.destinationIP))
        return ipheader

    # Extracts the received IP Header
    def extract(self, raw_packet):
        ipheader = struct.unpack('!BBHHHBBH4s4s', raw_packet)
        version_ihl = ipheader[0]
        self.version = version_ihl >> 4
        #self.ihl = version_ihl & 0xF

        self.ihl = version_ihl & 0xF
        self.tos = ipheader[1]
        self.totalLength = ipheader[2]
        self.id = ipheader[3]
        off = ipheader[4]
        self.flags = off >> 13
        self.offset = off & 0x1FFF
        self.ttl = ipheader[5]
        self.protocol = ipheader[6]
        self.checksum = ipheader[7]
        self.sourceIP = socket.inet_ntoa(ipheader[8])
        self.destinationIP = socket.inet_ntoa(ipheader[9])