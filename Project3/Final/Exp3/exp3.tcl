#Create a simulator object
set ns [new Simulator]

#Define different colors for data flows (for NAM)
$ns color 1 Blue
$ns color 2 Red

set variant [lindex $argv 0]
set queingAlgo [lindex $argv 1]

#Open the trace file (before you start the experiment!)
set tf [open Exp3-${variant}-${queingAlgo}-traceresults.tr w]
$ns trace-all $tf

#set nf [open exp3_nam.nam w]
#$ns namtrace-all $nf

proc finish {} {
        global ns tf
        $ns flush-trace
        #Close the NAM trace file
        close $tf
        #Execute NAM on the trace file
        #exec nam exp3_nam.nam &
        exit 0
}

#set nodes

set N1 [$ns node]
set N2 [$ns node]
set N3 [$ns node]
set N4 [$ns node]
set N5 [$ns node]
set N6 [$ns node]

#set links

$ns duplex-link $N1 $N2 10Mb 10ms $queingAlgo
$ns duplex-link $N5 $N2 10Mb 10ms $queingAlgo
$ns duplex-link $N2 $N3 10Mb 10ms $queingAlgo
$ns duplex-link $N4 $N3 10Mb 10ms $queingAlgo
$ns duplex-link $N6 $N3 10Mb 10ms $queingAlgo


#Set Queue Size of link (n2-n3) to 10
$ns queue-limit $N1 $N2 10
$ns queue-limit $N5 $N2 10
$ns queue-limit $N2 $N3 10
$ns queue-limit $N4 $N3 10
$ns queue-limit $N6 $N3 10


#Give node position (for NAM)

$ns duplex-link-op $N1 $N2 orient right-down
$ns duplex-link-op $N5 $N2 orient right-up
$ns duplex-link-op $N2 $N3 orient right
$ns duplex-link-op $N4 $N3 orient left-down
$ns duplex-link-op $N6 $N3 orient left-up

#Setup a TCP conncection
if {$variant eq "SACK"} {
	set tcp [new Agent/TCP/Sack1]
	set sink [new Agent/TCPSink/Sack1]
} elseif {$variant eq "Reno"} {
	set tcp [new Agent/TCP/Reno]
	set sink [new Agent/TCPSink]
}
$tcp set class_ 1
$ns attach-agent $N1 $tcp
$ns attach-agent $N4 $sink
$ns connect $tcp $sink
$tcp set fid_ 1


#Setup a FTP over TCP connection
set ftp [new Application/FTP]
$ftp attach-agent $tcp
$ftp set type_ FTP


#Setup a UDP connection
set udp [new Agent/UDP]
$ns attach-agent $N5 $udp
set null [new Agent/Null]
$ns attach-agent $N6 $null
$ns connect $udp $null
$udp set fid_ 2

#Setup a CBR over UDP connection
set cbr [new Application/Traffic/CBR]
$cbr attach-agent $udp
$cbr set type_ CBR
$cbr set packet_size_ 1000

$cbr set rate_ 6mb
$cbr set random_ false

#Schedule events for the CBR and FTP agents
$ns at 0.0 "$ftp start"
$ns at 10.0 "$cbr start"
$ns at 44.0 "$cbr stop"
$ns at 55.0 "$ftp stop"


# Call the finish procedure after 5 seconds of simulation time
$ns at 55.0 "finish"


#Run the simulation
$ns run

# Close the trace file (after you finish the experiment!)
close $tf

