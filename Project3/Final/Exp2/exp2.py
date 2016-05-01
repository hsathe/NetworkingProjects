'''
Created on Feb 26, 2016

@author: Harshad Sathe, Kaustubh Pande

'''
from subprocess import call
TCPVariants = ['Reno-Reno','Newreno-Reno','Vegas-Vegas','Newreno-Vegas']
class FairnessEvaluation():
    
    # Calculates the throughput for given pair variants.
    # This method calculates the throughput based on the time taken to receive first byte to the last byte.
    def getThroughput(self,fileName):
        
        fileHandle = open(fileName,'r')
        
        receivedPacket_size = 0.0
        receivedPacket_size_1 = 0
        destination_1 = "3"
        destination_2 = "5"
        timeList_1 = []
        timeList_2 = []
        for line in fileHandle:
            header = line.split()
            event = header[0]
            time = header[1]
            flowId = header[7]
            toNode = header[3]
            pkt_size = header[5]
            
            # For TCP flow N1-N4
            if flowId == "1":
                
                if event is 'r' and toNode is destination_1:
                                       
                    timeList_1.append(float(time))
                    
                    receivedPacket_size = receivedPacket_size + int(pkt_size)
            #For TCP flow N5-N6        
            if flowId == "3":
                if event is 'r' and toNode is destination_2:
                    
                    timeList_2.append(float(time))
                    receivedPacket_size_1 += int(pkt_size)
                            
        start_time = min(timeList_1)
        end_time = max(timeList_1)
        time_difference = end_time - start_time
        
        start_time_1 = min(timeList_2)
        end_time_1= max(timeList_2)
        time_difference_1 = end_time_1 - start_time_1
        
        receivedPacket_size_bits = receivedPacket_size * 8
        throughput_val =  receivedPacket_size_bits / time_difference
        
        receivedPacket_size_1_bits = receivedPacket_size_1 * 8
        throughput_val_1 = receivedPacket_size_1_bits / time_difference_1

        return str(throughput_val / 1000000) + '\t' + str(throughput_val_1 / 1000000)
    
    # Calculates the packet drop rate for the given TCP pair under congestion.
    # We determine the drop rate by drop rate / totalPackets sent. 
    def getDropRate(self,fileName):
        fileHandle = open(fileName,'r')
        sentPackets_1 = 0.0
        sentPackets_2 = 0.0
        drop_packet_1 = 0.0
        drop_packet_2  = 0.0
        for line in fileHandle:
            header = line.split()
            event = header[0]
            flowId = header[7]
            fromNode = header[2]
            
            # For TCP flow N1-N4
            if flowId is "1":
                if event is "+" and fromNode is "0":
                    sentPackets_1 += 1
                if event == "d":
                    drop_packet_1 += 1
            #For TCP flow N5-N6 
            elif flowId is "3":
                if event is "+" and fromNode is "4":
                    sentPackets_2 +=1 
                if event == "d":
                    drop_packet_2 += 1
        
        drop_rate1 = drop_packet_1 / sentPackets_1 
        
        drop_rate2 = drop_packet_2 / sentPackets_2
        
        return str(drop_rate1) + '\t' + str(drop_rate2)
    
    
    # Calculates the latency of the two TCP pairs under congestion.
    # We determine the latency by the formula TotalRTT / Total packet sent for each flow.
    # Total RTT is the difference between the packet start time to packet ack time
    def getLatency(self, fileName):
        fp = open(fileName)
        
        sentPacketsDict_1 = {}
        totalPackets_1 = 0
        totalRTT_1 = 0.0
        
        sentPacketsDict_2 = {}
        totalPackets_2 = 0
        totalRTT_2 = 0.0
        
        for each in fp:
            header = each.split()
            event = header[0]
            flowId = header[7]
            fromNode = header[2]
            toNode = header[3]
            seqNumber = header[10]
            pkt_type = header[4]
            time = header[1]
            #For TCP flow N1-N4 
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
            #For TCP flow N5-N6 
            elif flowId == "3":
                if event == "+" and int(fromNode) == 4:
                        sentPacketsDict_2[seqNumber] = float(time)
                if pkt_type == "ack":
                    if int(toNode) == 4: 
                        if seqNumber in sentPacketsDict_2: 
                            startTime_1 = sentPacketsDict_2[seqNumber]
                            finalTime_1 = float(time)
                            totalRTT_2 += (finalTime_1 - startTime_1)
                            totalPackets_2 += 1
                        
        latency_1 = totalRTT_1 / totalPackets_1
        
        latency_2 = totalRTT_2 / totalPackets_2
        
        return str(latency_1) + '\t' + str(latency_2)
          

def main():
        fe = FairnessEvaluation()

        for variants in TCPVariants:
            variant = variants.split('-')
            variant1 = variant[0]
            variant2 = variant[1]
            for packet_rate in range(1,11):
                call(["/course/cs4700f12/ns-allinone-2.35/bin/ns", "exp2.tcl", variant1, variant2, str(packet_rate)])
                
                fileName = "Exp2-"+variant1+"-"+variant2+"-traceresults-at-"+str(packet_rate)+".tr"
                
                fileHandle = open('Exp2-'+variant1+"-"+variant2+'-throughput.txt','a+')
                fileHandle.write(str(packet_rate) + '\t' + fe.getThroughput(fileName) + '\n');
                
                fileHandle_drop = open('Exp2-'+variant1+"-"+variant2+'-drop_rate.txt','a+')
                fileHandle_drop.write(str(packet_rate) + '\t' + fe.getDropRate(fileName) + '\n');
                
                fileHandle_latency = open('Exp2-'+variant1+"-"+variant2+'-latency.txt','a+')
                fileHandle_latency.write(str(packet_rate) + '\t' + fe.getLatency(fileName) + '\n');
        
        fileHandle.close()
        fileHandle_drop.close()
        fileHandle_latency.close()
        
if __name__ == '__main__':
    main()
    
