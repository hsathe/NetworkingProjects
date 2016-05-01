'''
Created on Feb 26, 2016

@author: Harshad Sathe, Kaustubh Pande

'''
from subprocess import call

QUEUEING_Algorithms = ['DropTail', 'RED']
TCP_Variants = ['Reno', 'SACK']

class QueueingInfluence():
    # Calculates the throughput for given TCP variants and specified Queuing algorithm
    # This method calculates the throughput based on the time taken to receive first byte to the last byte.
    def throughput(self,fileName,tcpVariant,queuingAlgo):
        
        fileHandle = open(fileName,'r')
        writeHandle = open("Exp3-"+tcpVariant+"-"+queuingAlgo+"-throughput.txt",'a+')
        
        sampling_frequency = 3.0
        clockTime = 1.0
        receivedTCPPacket_size = 0.0
        receivedCBRPacket_size = 0
        destination_1 = "3"
        destination_2 = "5"
        throughput_val_TCP = 0.0
        throughput_val_CBR = 0.0
        for line in fileHandle:
            header = line.split()
            event = header[0]
            time = float(header[1])
            flowId = header[7]
            toNode = header[3]
            pkt_size = header[5]
            
            if flowId == "1":
                if event is 'r' and toNode is destination_1:
                    receivedTCPPacket_size = receivedTCPPacket_size + int(pkt_size)
            # CBR        
            if flowId == "2":
                if event is 'r' and toNode is destination_2:
                    receivedCBRPacket_size += int(pkt_size)
            
            if (time - clockTime) > sampling_frequency:
                throughput_val_TCP =  receivedTCPPacket_size * 8 / sampling_frequency / 1000000
                throughput_val_CBR =  receivedCBRPacket_size * 8 / sampling_frequency / 1000000
                
                writeHandle.write(str(clockTime) + "\t" + str(throughput_val_TCP) + "\t" + str(throughput_val_CBR) + "\n")
                
                clockTime += sampling_frequency
                receivedTCPPacket_size = 0
                receivedCBRPacket_size = 0
        writeHandle.write(str(clockTime) + "\t" + str(throughput_val_TCP) + "\t" + str(throughput_val_CBR) + "\n")
        writeHandle.close()
        fileHandle.close()
    
    # Calculates the latency of the two TCP pairs for specified queuing algorithm.
    # We determine the latency by the formula TotalRTT / Total packet sent for each flow.
    # Total RTT is the difference between the packet start time to packet ack time
    def getLatency(self, fileName,tcpVariant,queuingAlgo):
        fp = open(fileName)
        writeHandle = open("Exp3-"+tcpVariant+"-"+queuingAlgo+"-latency.txt",'a+')
        
        sentPacketsDict_1 = {}
        totalPackets_1 = 0
        totalRTT_1 = 0.0
        
        
        for each in fp:
            header = each.split()
            event = header[0]
            flowId = header[7]
            fromNode = header[2]
            toNode = header[3]
            seqNumber = header[10]
            pkt_type = header[4]
            time = header[1]
            
            if flowId == "1":
                if event == "+" and int(fromNode) == 0:
                    sentPacketsDict_1[seqNumber] = float(time)
                if pkt_type == "ack":
                    if int(toNode) == 0: 
                        if seqNumber in sentPacketsDict_1:
                            startTime = sentPacketsDict_1[seqNumber]
                            finalTime = float(time)
                            totalRTT_1 += (finalTime - startTime)
                            totalPackets_1 += 1
                        
        latency_1 = totalRTT_1 / totalPackets_1
        
        writeHandle.write(str(latency_1))
        

def main():
        qi = QueueingInfluence()
        
        for variant in TCP_Variants:
            for queue_algo in QUEUEING_Algorithms:
                call(["/course/cs4700f12/ns-allinone-2.35/bin/ns", "exp3.tcl", variant, queue_algo])

                fileName = "Exp3-"+variant+"-"+queue_algo+"-traceresults.tr"
                qi.throughput(fileName,variant,queue_algo);
                qi.getLatency(fileName,variant,queue_algo)
                
                
        
if __name__ == '__main__':
    main()
    
