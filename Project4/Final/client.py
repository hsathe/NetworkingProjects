'''
Authors: Kaustubh S Pande/ Harshad Sathe

'''
import socket
import struct
import fcntl
import sys
from IPHeader import IPHeader
from TCPHeader import *
import random
import time


class RawSocket:
    # Finds the IP address of the source machine
    def getLocalhostIP(self):
        ip = ""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #Returns correct address to which the socket is bound
            s.connect(('ccs.neu.edu', 80))
            ip = s.getsockname()[0]
        except:
            print "Error connecting to Remote server. Please check your Network Connection and try again."
            sys.exit(2)
        return ip

    # Finds the IP of the destination machine
    def getDestinationIP(self):

        if len(sys.argv) != 2:
            sys.exit('Illegal Arguments.')
        urlraw = sys.argv[1]

        # Verify the input URL
        self.url = self.getCorrectURL(urlraw)
        destinationIP = ""
        self.urlHostName = self.url.split("/")[2]
        try:
            destinationIP = socket.gethostbyname(self.urlHostName)
        except:
            print "Error connecting to remote server. Please check your Network Connection and try again"
            sys.exit(2)
        return destinationIP

    #Verify the input URL and correct it, if required
    def getCorrectURL(self, url):

        if "http://" not in url:
            url = "http://" + url
        if url.endswith("/"):
            return url
        else:
            spliturl = url.split("/")
            lastelement = spliturl[len(spliturl) - 1]
            dotSplit = lastelement.split(".")
            if len(dotSplit) > 2 or len(dotSplit) == 1:
                url = url + "/"
                return url

            return url

    # Creates a Send Raw Socket for sending ACK, FIN
    def getSendRawSocket(self):
        try:
            sendSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        except:
            print "Error in socket creation"
            sys.exit(1)
        return sendSocket

    # Creates a Receive Raw Socket for receiving data, ACK, FIN flags
    def getReceiveRawSocket(self):
        try:
            receiveSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        except:
            print "Error creating receive socket"
            sys.exit(2)
        return receiveSocket

    # Finds available port numbers on the machine to bind
    def getOpenPortNumber(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))
        sock.listen(1)
        portNum = sock.getsockname()[1]
        sock.close()
        return portNum

    # Calculates checksum to verify the packet contents
    def calculateCheckSum(self, data):
        checksum = 0

        if ((len(data) % 2) != 0):
            for i in range(0, len(data) - 1, 2):
                word = ord(data[i]) + (ord(data[i + 1]) << 8)
                checksum += word
            checksum += socket.ntohs(0xFF00) & (ord(data[(len(data)-1)]))
        else:
            for i in range(0, len(data), 2):
                word = ord(data[i]) + (ord(data[i + 1]) << 8)
                checksum += word

        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += (checksum >> 16)

        checksum = ~checksum & 0xffff

        return checksum


    # Begin Handshake, sends SYN packet to server
    def sendSYNPacket(self, sendSock, localhostIP, destinationIP):

        self.ip_packet_ID = 10
        self.seq_num = 1050
        self.current_ack_no = 0

        self.sourcePortNum = self.getOpenPortNumber()
        self.destinationPortNum = 80

        SYNPacket = self.buildSYNPacket(localhostIP, destinationIP)
        sendSock.sendto(SYNPacket, (destinationIP, 80))

        self.receiveSYNACKPacket(sendSock, SYNPacket, localhostIP, destinationIP)

    # Helper function to build SYN Packet to be sent to the server
    def buildSYNPacket(self, localhostIP, destinationIP):

        IPHeaderObj = IPHeader(localhostIP, destinationIP, self.ip_packet_ID)
        ipHeader = IPHeaderObj.build()
        userData = ""

        TCPObj = TCPHeader()

        #Set the SYN Flag
        TCPObj.setValues(self.sourcePortNum, self.destinationPortNum, self.seq_num, self.current_ack_no, 1, 0, 0, userData)
        tcpHeader = TCPObj.build(localhostIP, destinationIP)

        SYNPacket = ipHeader + tcpHeader + userData
        return SYNPacket

    # Server sends the SYN/ACK packet, this packet is received at the receiveSock
    def receiveSYNACKPacket(self, sendSock, SYNPacket, localhostIP, destinationIP):
        self.ack_packet = ""
        self.cwnd = 1
        self.startTime = 0
        user_request = ""

        receiveSock = self.getReceiveRawSocket()
        self.startTime = time.clock()

        # Receives packet
        while True:
            receiveSock.settimeout(180)
            try:
                receivedPacket = receiveSock.recvfrom(65565)
            except:
                print "Exception in receiving SYN/ACK packet"
                sendSock.close()
                receiveSock.close()
                sys.exit(2)

            packet = receivedPacket[0]

            received_IPHeader = packet[0:20]
            ipheader = IPHeader(0, 0, 0)
            ipheader.extract(received_IPHeader)

            checksum = self.calculateCheckSum(received_IPHeader)

            time_elapsed = time.clock() - self.startTime

            if time_elapsed > 60:

                sendSock.sendto(SYNPacket, (destinationIP, self.destinationPortNum))
                self.startTime = time.clock()

            if (ipheader.protocol == 6) and (checksum == 0) and (ipheader.sourceIP == destinationIP) and (ipheader.destinationIP == localhostIP):
                get_TCPHeader = self.getTCPHeaderFromIPHeader(packet, ipheader)
                tcpheader = TCPHeader()
                tcpheader.extract(get_TCPHeader)

                if (tcpheader.sourcePort == self.destinationPortNum and tcpheader.destPort == self.sourcePortNum and tcpheader.ack_flg == 1 and tcpheader.ackNo == self.seq_num + 1 and not tcpheader.rst_flg):
                    self.seq_num = tcpheader.ackNo
                    self.current_ack_no = tcpheader.sequenceNo + 1
                    self.ip_packet_ID = self.ip_packet_ID + 1
                    ipheader1 = self.getIPHeader(localhostIP, destinationIP, self.ip_packet_ID)
                    user_request = self.getHttpGETRequest(self.url, self.urlHostName)

                    tcp_header1 = self.getTCPHeader(localhostIP, destinationIP, user_request)
                    self.ack_packet = ipheader1 + tcp_header1 + user_request
                    sendSock.sendto(self.ack_packet, (destinationIP, 80))
                    break
        # Handshake Completed, start downloading file from the server
        self.getMessagesFromServer(time.clock(), user_request, localhostIP, destinationIP, sendSock, receiveSock)

    # Helper Function to build the TCPHeader, with ACK flag set
    def getTCPHeader(self, localhostIP, destinationIP, user_request):
        tcpheader_obj = TCPHeader()
        tcpheader_obj.setValues(self.sourcePortNum, self.destinationPortNum, self.seq_num, self.current_ack_no, 0, 1, 0, user_request)

        tcp_header = tcpheader_obj.build(localhostIP, destinationIP)

        return tcp_header

    # Helper Function to build the IPHeader
    def getIPHeader(self, localhostIP, destinationIP, ip_packet_ID):

        ipheader_obj = IPHeader(localhostIP, destinationIP, ip_packet_ID)
        ipheader = ipheader_obj.build()
        return ipheader

    # Helper Function, to strip the TCP header from IP Packet
    def getTCPHeaderFromIPHeader(self, packet, ipheader):
        tcp_header_start = ipheader.ihl * 4
        get_TCPHeader = packet[tcp_header_start:tcp_header_start + 20]
        return get_TCPHeader

    # Method to receive messages from server. Packets will be received at receiveSock, ACK will be sent on sendSock
    def getMessagesFromServer(self, start_Time, user_request, localhostIP, destinationIP, sendSock, receiveSock):

        self.page_content_dict = {}

        roundTripTime = time.clock()

        http_ack_flg = False
        self.seq_num = self.seq_num + len(user_request)

        while True:
            receiveSock.settimeout(180)
            try:
                receivedPacket = receiveSock.recvfrom(65565)
            except receiveSock.timeout:
                print "Socket timed out. No packet received in 3 minutes"
                sendSock.close()
                receiveSock.close()
                sys.exit(2)

            spent_Time = time.clock() - start_Time
            # Resend if the packet is not received before 1min
            if spent_Time > 60 and not http_ack_flg:

                sendSock.sendto(self.ack_packet, (destinationIP, 80))
                start_Time = time.clock()

            packet = receivedPacket[0]
            received_IPHeader = packet[0:20]
            ipheader = IPHeader(0, 0, 0)
            ipheader.extract(received_IPHeader)

            checksum = self.calculateCheckSum(received_IPHeader)
            # Checks if the protocol is TCP, if the server IP is the source IP in the packet, if the localhostIP is the destination in the packet
            if ipheader.protocol == 6 and ipheader.sourceIP == destinationIP and ipheader.destinationIP == localhostIP and checksum == 0:

                get_TCPHeader = self.getTCPHeaderFromIPHeader(packet, ipheader)
                tcpheader = TCPHeader()
                tcpheader.extract(get_TCPHeader)

                # Strip of header length, and gets the actual data
                header_length = (tcpheader.HL_Offset * 4) + (ipheader.ihl * 4)
                message_length = ipheader.totalLength - header_length
                actual_page_content = packet[header_length:]

                self.checkcwnd(tcpheader)

                # Checks valid sourcePort,destPort in TCP header
                if tcpheader.sourcePort == self.destinationPortNum and tcpheader.destPort == self.sourcePortNum and tcpheader.ackNo == self.seq_num:
                    time_spent = time.clock() - roundTripTime

                    if (time_spent > 180):
                        print "No packet received from server for 3 minutes. Terminating program. "
                        sendSock.close()
                        receiveSock.close()
                        sys.exit(2)

                    roundTripTime = time.clock()
                    # Indicates end of data
                    if tcpheader.fin_flg == 1:
                        self.current_ack_no += 1
                        self.page_content_dict[tcpheader.sequenceNo] = actual_page_content
                        self.startTearDown(self.current_ack_no, localhostIP, destinationIP, sendSock, receiveSock)
                        break
                    # Continue to receive data, indicates this is an ACK
                    if tcpheader.ack_flg == 1 and http_ack_flg == False and tcpheader.ackNo == self.seq_num:
                        http_ack_flg = True
                        continue
                    if tcpheader.syn_flg == 1 and tcpheader.ack_flg == 1:
                        continue
                    else:
                        # Stores Data in the dictionary in sequenceNo:data format
                        if self.page_content_dict.has_key(tcpheader.sequenceNo):
                            self.sendAckToServer(message_length + tcpheader.sequenceNo, localhostIP, destinationIP, sendSock)
                        else:
                            self.current_ack_no = self.current_ack_no + message_length
                            self.page_content_dict[tcpheader.sequenceNo] = actual_page_content
                            self.sendAckToServer(self.current_ack_no, localhostIP, destinationIP, sendSock)

    # Handle Congestion Window
    def checkcwnd(self, tcpheader):
        if tcpheader.ack_flg == 1:
            if self.cwnd <= 1000:
                self.cwnd += 1
            else:
                self.cwnd = 1

    # Respond to the received packet by sending ACK to server
    def sendAckToServer(self, local_current_ack_no, localhostIP, destinationIP, sendSock):

        self.ip_packet_ID = self.ip_packet_ID + 1
        ipheader = self.getIPHeader(localhostIP, destinationIP, self.ip_packet_ID)

        tcpobj = TCPHeader()
        tcpobj.setValues(self.sourcePortNum, self.destinationPortNum, self.seq_num, local_current_ack_no, 0, 1, 0, "")
        tcpheader = tcpobj.build(localhostIP, destinationIP)

        packet = ipheader + tcpheader + ""

        sendSock.sendto(packet, (destinationIP, self.destinationPortNum))



    # Creates a file, filename is used based on the provided URL
    def writeToFile(self):
        fileName = self.getFileName1(self.url)
        #print "file name " + fileName
        pageText = ""
        # Sorts the dictionary according to the sequence numbers.
        sortedList = sorted(self.page_content_dict)
        for key in sortedList:
            pageText = self.page_content_dict[key]
            break

        if self.isValidPage(pageText):

            flag = False
            for key in sortedList:
                if not flag:
                    self.page_content_dict[key] = self.removeHeader(self.page_content_dict[key])
                    flag = True
                    outputFile = open(fileName, "w+")
                outputFile.write(self.page_content_dict[key])
        else:
            print "Invalid Status Code received, exiting."
            sys.exit(2)

    # Removes the header content from the first packet
    def removeHeader(self, pageText):
        return pageText.split("\r\n\r\n")[1]

    # Handles HTTP requests, only processes status 200
    def isValidPage(self, pageText):
        header = pageText.split("\r\n\r\n")[0]

        if "HTTP/1.1 200" not in header:
            return False
        return True

    # Finds the filename, for the file to be created.
    def getFileName1(self, url):
        if url.endswith("/"):
            spliturl = url.split("/")
            lastelement = spliturl[len(spliturl) - 1]
            if lastelement == "":
                lastelement = spliturl[len(spliturl) - 2]
            dotSplit = lastelement.split(".")
            if len(dotSplit) > 2:
                return "index.html"
            else:
                return lastelement
        else:
            spliturl = url.split("/")
            lastelement = spliturl[len(spliturl) - 1]
            return lastelement

    # Sends HTTP GET Request
    def getHttpGETRequest(self, url, hostname):
        relative_path = self.get_relative_path(url, hostname)
        if len(relative_path) % 2 == 1:
            relative_path = relative_path + " "
        getRequest = "GET " + relative_path + " HTTP/1.0\r\n"
        getRequest = getRequest + "Host: " + hostname + "\r\n" + '\n' + "\r\n"
        return getRequest

    # Strips domain value from the given URL
    def get_relative_path(self, givenURL, hostname):
        start_position = givenURL.find(hostname) + len(hostname)
        return givenURL[start_position:]



    # Handles connection termination, when the server sends FIN flag
    def startTearDown(self, local_current_ack_no, localhostIP, destinationIP, sendSock, receiveSock):
        # Sends ACK to server of the received packet content
        self.sendAckToServer(local_current_ack_no, localhostIP, destinationIP, sendSock)

        self.ip_packet_ID = self.ip_packet_ID + 1
        ipheader = self.getIPHeader(localhostIP, destinationIP, self.ip_packet_ID)

        tcpobj = TCPHeader()
        tcpobj.setValues(self.sourcePortNum, self.destinationPortNum, self.seq_num, local_current_ack_no, 0, 1, 1, "")
        tcpheader = tcpobj.build(localhostIP, destinationIP)

        packet = ipheader + tcpheader + ""

        sendSock.sendto(packet, (destinationIP, 80))
        start_time = time.clock()

        while True:
            try:
                receivedPacket = receiveSock.recvfrom(65565)
            except:
                print "Exception in tear down"
                sys.exit(2)

            packetData = receivedPacket[0]

            received_IPHeader = packetData[0:20]
            ipheader = IPHeader(0, 0, 0)
            ipheader.extract(received_IPHeader)

            checksum = self.calculateCheckSum(received_IPHeader)

            spent_Time = time.clock() - start_time

            # Resend if time exceeds 1min
            if spent_Time > 60:
                sendSock.sendto(packet, (destinationIP, 80))
                start_time = time.clock()
            # Checks if the protocol is 6, and checks the source and destination in the IP Packet
            if ipheader.protocol == 6 and ipheader.sourceIP == destinationIP and ipheader.destinationIP == localhostIP and checksum == 0:
                get_TCPHeader = self.getTCPHeaderFromIPHeader(packetData, ipheader)
                tcpheader = TCPHeader()
                tcpheader.extract(get_TCPHeader)

                if tcpheader.sourcePort == self.destinationPortNum and tcpheader.destPort == self.sourcePortNum and tcpheader.ackNo == self.seq_num + 1:
                    return


def main():
    r = RawSocket()
    localHostIP = r.getLocalhostIP()
    destinationIP = r.getDestinationIP()
    sendSock = r.getSendRawSocket()

    r.sendSYNPacket(sendSock, localHostIP, destinationIP)
    r.writeToFile()

if __name__ == "__main__":
    main()
