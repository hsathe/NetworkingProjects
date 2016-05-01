'''
Created for Roll you onw CDN project
@authors: Kaustubh Pande, Harshad Sathe

'''
from SocketServer import BaseRequestHandler, ThreadingUDPServer
import struct
import socket
from math import sin, atan2, radians, cos, sqrt
import commands
import re
import random
import sys

# Global Variables
TYPE_A = 1
TYPE_AAAA = 28
CLASS_IN = 1
INF = 'inf'
MAX_VAL = 1e30000
CURL_CMD = 'curl ipinfo.io/'
EARTH_RADIUS = 6373.0
client_mappings = {}
CDN = 'cs5700cdn.example.com'

# This dictionary maintains mappings for each replica server and its location(Found using maps API)
replica_ip_location_mapping_dict = {"54.85.32.37":"39.0335,-77.4838",
                    "54.193.70.31":"37.3394,-121.8950",
                    "52.38.67.246":"45.7788,-119.5290",
                    "52.51.20.200":"53.3331,-6.2489",
                    "52.29.65.165":"50.1167,8.6833",
                    "52.63.206.143":"-33.8678,151.2073",
                    "52.196.70.227":"35.6850,139.7514",
                    "54.169.117.213":"1.2931,103.8558",
                    "54.233.185.94":"-23.5475,-46.6361"}

# Class to build, extract the incoming query
class DNSQuery():
    def __init__(self):
        self.query_name = ''
        self.query_type = 0
        self.query_class = 0

    # Builds the DNS Packet
    def build_DNS_query(self, domain):
        self.query_name = domain
        dns_query = ''.join(chr(len(x)) + x for x in domain.split('.'))
        dns_query = dns_query + '\x00'
        final_query = dns_query + struct.pack('>HH', self.query_type, self.query_class)
        return final_query

    # Extracts the DNS Packet
    def extract(self,data):
        global CDN
        dnsHeader = struct.unpack('>HH', data[-4:])
        self.query_type = dnsHeader[0]
        self.query_class = dnsHeader[1]
        qname = data[:-4]
        index = 0
        tempName = []
        try:
            while True:
                countReq = ord(qname[index])
                if countReq == 0:
                    break
                index = index + 1
                tempName.append(qname[index:index + countReq])
                index = index + countReq

            self.query_name = '.'.join(tempName)
        except:
            self.query_name = CDN

# Creates an answer to the request DNS query
class DNS_Answer_class():
    # Initialize Header Format
    def __init__(self):
        self.answer_name = 0
        self.answer_type = 0
        self.answer_class = 0
        self.ttl = 0
        self.addr = ''
        self.len = 0

    # Builds a DNS Answer sets the flags and injects data
    def build_DNS_answer(self, ip):
        self.answer_name = 0xC00C
        self.answer_type = 0x0001
        self.answer_class = 0x0001
        self.ttl = 60  # time to live
        self.addr = ip
        self.len = 4
        answer = struct.pack('>HHHLH4s', self.answer_name, self.answer_type, self.answer_class,
                          self.ttl, self.len, socket.inet_aton(self.addr))
        return answer

# Class builds the DNS Packet
class DNS_packet_class() :
    # Initializes all the flags and header values to default
    def __init__(self):
        self.id = 0
        self.secondLayerFlags = 0
        self.qdcount = 0
        self.ancount = 0
        self.nscount = 0
        self.arcount = 0
        self.dnsQuery = DNSQuery()
        self.dnsAnswer = DNS_Answer_class()
    # Creates a DNS answer, sets the required flags and builds answer
    def create_dns_answer(self, ip, domain):
        self.dnsAnswer = DNS_Answer_class()
        self.ancount = 1
        self.flags = 0x8180
        packet = self.create_packet(domain)
        packet = packet + self.dnsAnswer.build_DNS_answer(ip)
        return packet

    # Create a packet
    def create_packet(self, domain):
        packet = struct.pack('>HHHHHH', self.id, self.secondLayerFlags, self.qdcount,
                             self.ancount, self.nscount, self.arcount)
        packet = packet + self.dnsQuery.build_DNS_query(domain)
        return packet

    # Extracts the header fields from the the DNS packets and initializes the current object
    def extract(self,packet):
        dns_packet = struct.unpack('>HHHHHH', packet[:12])
        self.id = dns_packet[0]
        self.secondLayerFlags = dns_packet[1]
        self.qdcount = dns_packet [2]
        self.ancount = dns_packet [3]
        self.nscount = dns_packet [4]
        self.arcount = dns_packet [5]
        self.dnsQuery = DNSQuery()
        self.dnsQuery.extract(packet[12:])
        self.dnsAnswer = None

# DNS handler class implements a BaseRequestHandler and listens for any incoming DNS resolution requests
class DNS_Handler_class(BaseRequestHandler):
    # Listens for any DNS requests
    def handle(self):
        request, socket = self.request
        request = request.strip()

        packetObj = DNS_packet_class()
        packetObj.extract(request)

        if packetObj.dnsQuery.query_type in (TYPE_A,TYPE_AAAA) and packetObj.dnsQuery.query_class == CLASS_IN:
            domain_name = packetObj.dnsQuery.query_name
            if domain_name == cdn_name :
                ip = self.get_best_replica_server()
                data = packetObj.create_dns_answer(ip,domain_name)
                socket.sendto(data, self.client_address)
            else:
                socket.sendto(request, self.client_address)
        else:
            socket.sendto(request, self.client_address)

    # Finds a best replica server, currently based on GeoLocation values
    def get_best_replica_server(self):
        try:
            global  replica_ip_location_mapping_dict
            client_ip = self.client_address[0]
            if client_ip not in client_mappings:

                try:
                    closestDistance = float(INF)
                except:
                    closestDistance= MAX_VAL

                client_location = self.getLocationData(client_ip)[0]
                closest_ip = None

                for replica_server in replica_ip_location_mapping_dict:
                    current_distance = self.calculateDistance(replica_ip_location_mapping_dict[replica_server],client_location)
                    if current_distance < closestDistance:
                        closestDistance = current_distance
                        closest_ip = replica_server

                client_mappings[client_ip] = closest_ip
            else:
                closest_ip = client_mappings[client_ip]

            return closest_ip
        except:
            closest_ip = random.choice(replica_ip_location_mapping_dict.keys())
            return closest_ip

    # Finds the current location of the client
    def getLocationData(self,client_ip):
        run_cmd = CURL_CMD + client_ip
        cmd_result = commands.getoutput(run_cmd)
        location_data = re.findall(r"\"loc\": \"(.*?)\"", cmd_result)
        return location_data

    # Calculates distance between the Client and each Replica Server. Returns distance value
    def calculateDistance(self,replica_location,client_location):
        client = client_location.split(",")
        replica = replica_location.split(",")

        client_latitude = float((client[0]))
        client_Longitude = float((client[1]))
        replica_Latitude = float((replica[0]))
        replica_Longitude = float((replica[1]))

        return self.distanceEquation(radians(client_latitude), radians(client_Longitude),radians(replica_Latitude),radians(replica_Longitude))

    # Based on the GeoLocation formula, it finds the distance between the client and replica servers. Returns
    def distanceEquation(self,client_latitude,client_Longitude,replica_Latitude,replica_Longitude):

        longitude = replica_Longitude - client_Longitude
        latitude = replica_Latitude - client_latitude

        sin_cos_product = sin(latitude / 2) * sin(latitude / 2) + cos(client_latitude) * cos(client_Longitude) * sin(longitude / 2) * sin(longitude / 2)
        val = 2 * atan2(sqrt(sin_cos_product), sqrt(1 - sin_cos_product))
        distance = EARTH_RADIUS * val

        return distance

# DNS Server Class, is a UDP Server, which handles the DNS Server on cs5700cdnproject.ccs.neu.edu
class DNS_Server_class(ThreadingUDPServer):
    def __init__(self, port_num):
        ThreadingUDPServer.__init__(self, ('',port_num), DNS_Handler_class)
        return

# Main function, which takes port and cdn name inputs and initializes the DNS Server to respond to DNS queries. Only cs5700cdn.example.com will be resolved
def main():
    global replica_ip_mapping_dict,cdn_name
    port_num = int(sys.argv[2])
    cdn_name = sys.argv[4]
    try:
        dnsserver = DNS_Server_class(port_num)
        dnsserver.serve_forever()
    except KeyboardInterrupt:
        dnsserver.shutdown()
        dnsserver.server_close()

if __name__ == '__main__':
    main()
