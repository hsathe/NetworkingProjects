#Create a simulator object
set ns [new Simulator]

#Input values of two TCP Variants and Packet Rate
set variant1 [lindex $argv 0]
set variant2 [lindex $argv 1]
set packet_rate [lindex $argv 2]

#Define different colors for data flows (for NAM)
$ns color 1 Blue
$ns color 2 Red

#Open the trace file (before you start the experiment!)
set tf [open Exp2-${variant1}-${variant2}-traceresults-at-${packet_rate}.tr w]
$ns trace-all $tf

#set nf [open exp2_nam.nam w]
#$ns namtrace-all $nf

proc finish {} {
        global ns tf tcp
        $ns flush-trace
        #Close the trace file
        close $tf
        #Execute NAM on the trace file
        #exec nam exp2_nam.nam &
        exit 0
}

#Create 6 nodes

set N1 [$ns node]
set N2 [$ns node]
set N3 [$ns node]
set N4 [$ns node]
set N5 [$ns node]
set N6 [$ns node]

#set links

$ns duplex-link $N1 $N2 10Mb 10ms DropTail
$ns duplex-link $N5 $N2 10Mb 10ms DropTail
$ns duplex-link $N2 $N3 10Mb 10ms DropTail
$ns duplex-link $N4 $N3 10Mb 10ms DropTail
$ns duplex-link $N6 $N3 10Mb 10ms DropTail


#Give node position (for NAM)
$ns duplex-link-op $N1 $N2 orient right-down
$ns duplex-link-op $N5 $N2 orient right-up
$ns duplex-link-op $N2 $N3 orient right
$ns duplex-link-op $N4 $N3 orient left-down
$ns duplex-link-op $N6 $N3 orient left-up


#Setup a TCP connection 1
# should accept command line
if {$variant1 eq "Reno"} {
	set tcp [new Agent/TCP/Reno]
} elseif {$variant1 eq "Newreno"} {
	set tcp [new Agent/TCP/Newreno]
} elseif {$variant1 eq "Vegas"} {
	set tcp [new Agent/TCP/Vegas]
}

$tcp set class_ 2
$ns attach-agent $N1 $tcp
set sink [new Agent/TCPSink]
$ns attach-agent $N4 $sink
$ns connect $tcp $sink
$tcp set fid_ 1


#Setup a TCP connection 2
if {$variant2 eq "Reno"} {
	set tcp_1 [new Agent/TCP/Reno]
} elseif {$variant2 eq "Vegas"} {
	set tcp_1 [new Agent/TCP/Vegas]
}

$tcp_1 set class_ 2
$ns attach-agent $N5 $tcp_1
set sink_1 [new Agent/TCPSink]
$ns attach-agent $N6 $sink_1
$ns connect $tcp_1 $sink_1
$tcp_1 set fid_ 3


#Setup a FTP over TCP connection 1
set ftp [new Application/FTP]
$ftp attach-agent $tcp
$ftp set type_ FTP

#Setup a FTP over TCP connection 2
set ftp_1 [new Application/FTP]
$ftp_1 attach-agent $tcp_1
$ftp_1 set type_ FTP

#Setup a UDP connection
set udp [new Agent/UDP]
$ns attach-agent $N2 $udp
set null [new Agent/Null]
$ns attach-agent $N3 $null
$ns connect $udp $null
$udp set fid_ 2

#Setup a CBR over UDP connection
set cbr [new Application/Traffic/CBR]
$cbr attach-agent $udp
$cbr set type_ CBR
$cbr set packet_size_ 1000

# This needs to be varied for this experiment
$cbr set rate_ ${packet_rate}mb
$cbr set random_ false

#Schedule events for the CBR and FTP agents
$ns at 0.0 "$cbr start"
$ns at 1.0 "$ftp start"
$ns at 1.0 "$ftp_1 start"
$ns at 10.0 "$ftp stop"
$ns at 10.0 "$ftp_1 stop"
$ns at 10.0 "$cbr stop"

# Call the finish procedure after 5 seconds of simulation time
$ns at 10.0 "finish"


#Run the simulation
$ns run

# Close the trace file (after you finish the experiment!)
close $tf

