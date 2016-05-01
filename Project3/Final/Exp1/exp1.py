'''
Created on Feb 25, 2016

@author: Kaustubh Pande, Harshad Sathe
'''

from subprocess import call


class Exp1(object):
    # Driver function to calculate throughput,drop rate and latency for TCP variants        
    def runScripts(self):
        self.TCPVariants = ['Tahoe', 'Reno', 'NewReno', 'Vegas']
        f1 = open("result_latency.txt", 'w')
        f2 = open("result_throughput.txt", 'w')
        f3 = open("result_dropRate.txt", 'w')
        
        f1.write("CBR Rate" + "\t" + "Tahoe" + "\t" + "Reno" + "\t" + "NewReno" + "\t" + "Vegas" + "\n")
        f2.write("CBR Rate" + "\t" + "Tahoe" + "\t" + "Reno" + "\t" + "NewReno" + "\t" + "Vegas" + "\n")
        f3.write("CBR Rate" + "\t" + "Tahoe" + "\t" + "Reno" + "\t" + "NewReno" + "\t" + "Vegas" + "\n")
        
        for rate in range(1, 11):
            str_latency = ''
            str_throughput = ''
            str_dropRate = ''
            for variant in self.TCPVariants:
                call(["/course/cs4700f12/ns-allinone-2.35/bin/ns", "exp1.tcl", variant, str(rate)])
                str_latency = str_latency + "\t" + str(self.getLatency(variant, rate)) + "\t"
                str_throughput = str_throughput + "\t" + str(self.getThroughput(variant, rate)) + "\t"
                str_dropRate = str_dropRate + "\t" + str(self.getPacketDropRate(variant, rate)) + "\t"
            f1.write(str(rate) + "\t" + str_latency + "\n")
            f2.write(str(rate) + "\t" + str_throughput + "\n")
            f3.write(str(rate) + "\t" + str_dropRate + "\n")
        f1.close()
        f2.close()
        f3.close()
        
        
    # Calculates the throughput for TCP variants.
    # This method calculates the throughput based on the time taken to receive first byte to the last byte.  
    def getThroughput(self, variant, rate):
        traceFileName = variant + "_trace_" + str(rate) + ".tr"
        fp = open(traceFileName)
        totalSize = 0.0
        timeList = []
        for each in fp:
            line = each.split()     
            if int(line[3]) == 3 and line[0] == "r":
                totalSize = totalSize + int(line[5])
                
                timeList.append(float(line[1]))
            
        sizeInBits = totalSize * 8
        firstPacketTime = min(timeList)
        lastPacketTime = max(timeList)
        timeDifference = lastPacketTime - firstPacketTime
        
        throughput = sizeInBits / timeDifference
        return str(throughput / 1000000)
        
    # Calculates the packet drop rate for TCP variants under congestion.
    # This method determines the drop rate by calculating drop rate / totalPackets sent. 
    def getPacketDropRate(self, variant, rate):
        traceFileName = variant + "_trace_" + str(rate)  +".tr"
        fp = open(traceFileName)
        dropPacketNum = 0.0
        sentPacketNum = 0
        receivedPackets = 0
        for each in fp:
            line = each.split()
            
            if (int(line[2]) == 0 and line[0] == "+"):
                
                sentPacketNum = sentPacketNum + 1
            if (int(line[3]) == 3 and line[0] == "r"):
                
                receivedPackets = receivedPackets + 1;
            if (line[0] == "d" and int(line[7]) == 1):
                
                dropPacketNum = dropPacketNum + 1
                
        dropRate = dropPacketNum / sentPacketNum
        return str(dropRate)
        
    # Calculates the latency of the TCP variants under congestion.
    # We determine the latency by the formula TotalRTT / Total packet sent for each flow.
    # Total RTT is the difference between the packet start time to packet ack time
    def getLatency(self, variant, rate):
        traceFileName = variant + "_trace_" + str(rate) +".tr"
        fp = open(traceFileName)
        sentPacketsDict = {}
        totalPackets = 0
        totalRTT = 0.0
        
        
        for each in fp:
            line = each.split()
             
            if line[0] == "+" and int(line[2]) == 0:
            
                sentPacketsDict[line[10]] = float(line[1])
        
        
            elif int(line[3]) == 0 and line[4] == "ack" : 
                if line[10] in sentPacketsDict:    
                    
                    startTime = sentPacketsDict[line[10]]
                    
                    finalTime = float(line[1])
                    totalRTT += (finalTime - startTime)
                    totalPackets += 1

        latency = totalRTT / totalPackets
        return latency

def main():
    
    e = Exp1()
    e.runScripts()
    
    
    
if __name__ == '__main__':
    main()
