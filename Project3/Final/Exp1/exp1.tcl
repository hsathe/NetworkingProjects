#Create a simulator object
set ns [new Simulator]

# Set TCP variant
set variant [lindex $argv 0]

# Set CBR Rate
set cbrRate [lindex $argv 1]

#Define different colors for data flows (for NAM)
$ns color 1 Blue
$ns color 2 Red

#Open the trace file (before you start the experiment!)
set tf [open ${variant}_trace_${cbrRate}.tr w]

#set tf [open trace_output}.tr w]
$ns trace-all $tf

#set nf [open exp1_nam.nam w]
#$ns namtrace-all $nf

proc finish {} {
        global ns tf
		#Close the NAM trace file
        #close $nf
        #Execute NAM on the trace file
        #exec nam exp1_nam.nam &
        $ns flush-trace
		close $tf
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

$ns duplex-link $N1 $N2 10Mb 2ms DropTail
$ns duplex-link $N5 $N2 10Mb 2ms DropTail
$ns duplex-link $N2 $N3 10Mb 2ms DropTail
$ns duplex-link $N4 $N3 10Mb 2ms DropTail
$ns duplex-link $N6 $N3 10Mb 2ms DropTail


#Set Queue Size of link (n2-n3) to 10
$ns queue-limit $N2 $N3 5


#Give node position (for NAM)

$ns duplex-link-op $N1 $N2 orient right-down
$ns duplex-link-op $N5 $N2 orient right-up
$ns duplex-link-op $N2 $N3 orient right
$ns duplex-link-op $N4 $N3 orient left-down
$ns duplex-link-op $N6 $N3 orient left-up


#Setup a TCP connection
if {$variant eq "Tahoe"} {
	set tcp [new Agent/TCP]
} elseif {$variant eq "Reno"} {
	set tcp [new Agent/TCP/Reno]
} elseif {$variant eq "NewReno"} {
	set tcp [new Agent/TCP/Newreno]
} elseif {$variant eq "Vegas"} {
	set tcp [new Agent/TCP/Vegas]
}



#set tcp [new Agent/TCP]
$tcp set class_ 2
$ns attach-agent $N1 $tcp
set sink [new Agent/TCPSink]
$ns attach-agent $N4 $sink
$ns connect $tcp $sink
$tcp set fid_ 1
#$tcp set packet_size_ 2000


#Setup a FTP over TCP connection
set ftp [new Application/FTP]
$ftp attach-agent $tcp
$ftp set type_ FTP


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
$cbr set packet_size_ 500

# This needs to be varied for this experiment

$cbr set rate_ ${cbrRate}mb	
$cbr set random_ false

#Schedule events for the CBR and FTP agents
$ns at 0.0 "$cbr start"
$ns at 1.0 "$ftp start"
$ns at 10.0 "$ftp stop"
$ns at 10.0 "$cbr stop"


# Call the finish procedure after 10 seconds of simulation time
$ns at 10.0 "finish"


#Run the simulation
$ns run

# Close the trace file (after you finish the experiment!)
close $tf

