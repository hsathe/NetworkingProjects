'''
Created on Jan 23, 2016

@author: Harshad Sathe, Kaustubh Pande
'''

#!/usr/bin/env python3 
# Import packages to support Socket, System and SSL functions
import socket
import sys
import ssl
from _ssl import CERT_NONE

# Global Variable defined to identify, if the Response received is a 'BYE' or any other message
# By default the value of the flag = 1. The value switches to 0 only if 'BYE' message is
# received from the HOST Server.
flag = 1

class Client:  
#    Creates a SSL or Non-SSL connection with the Server host name at given PORT number.
#    Default PORT=27993 for Non-SSL connection and PORT=27994 for SSL connection. 
#    Any other PORTs are invalid
    def create_Connection(self):
        self.cmdhost = sys.argv
        try:
            if "-s" in self.cmdhost:
                if (len(self.cmdhost) == 4):
                    HOSTSSL = str(self.cmdhost[2])
                    PORTSSL = 27994
                    self.get_SSL_Connection(HOSTSSL, PORTSSL)      
                elif (len(self.cmdhost) == 5):
                    HOSTSSL = str(self.cmdhost[3])
                    PORTSSL = int(self.cmdhost[1])
                    if (PORTSSL == 27993 or PORTSSL == 27994):
                        self.get_SSL_Connection(HOSTSSL, PORTSSL)
                    else:
                        print "Invalid Port number"
                        sys.exit(2)
                else:
                    print "Invalid number of Arguments"
                    sys.exit(2)
            else:
                if (len(self.cmdhost) == 3):
                    HOST = str(self.cmdhost[1])
                    PORTNUM = 27993
                    self.get_Connection(HOST, PORTNUM)
                elif (len(self.cmdhost) == 4):
                    HOST = str(self.cmdhost[2])
                    PORTNUM = int(self.cmdhost[1])
                    if (PORTNUM == 27993 or PORTNUM == 27994):
                        self.get_Connection(HOST, PORTNUM)  
                    else:
                        print "Invalid Port Number"
                        sys.exit(2)            
                else:
                    print "Invalid number of Arguments"
                    sys.exit(2)
        except SystemExit:
            sys.exit(2)
        except:
            print "Unable to connect to the Server"
            sys.exit(2)
    
    
#    Creates a SSL Connection with the Host Server at default PORT=27994
    def get_SSL_Connection(self, HOSTSSL, PORTSSL):
        try:
            self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.clientSocket = ssl.wrap_socket(self.soc, cert_reqs=CERT_NONE)
            server_address = (HOSTSSL, PORTSSL)
            self.clientSocket.connect(server_address)
        except:
            print "Unable to connect the hostname"
            sys.exit(2)
     
#    Creates a Non-SSL Connection with the Host Server at default PORT=27993        
    def get_Connection(self, HOST, PORTNUM):
        try:
            self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (HOST, PORTNUM)
            self.clientSocket.connect(server_address)
        except:
            print "Unable to connect the hostname"
            sys.exit(2)
     
#    Sends a HELLO message to the Server. 
#    Format of the HELLO message is: cs5700spring2016 HELLO [your NEU ID]\n
    def send_Hello_Msg(self):
        if "-s" in self.cmdhost:
            if (len(self.cmdhost) == 4):
                NEUID = str(self.cmdhost[3])
            else:
                NEUID = str(self.cmdhost[4])
        else:
            if (len(self.cmdhost) == 3):
                NEUID = str(self.cmdhost[2])
            else:
                NEUID = str(self.cmdhost[3]) 
        try:
            message = 'cs5700spring2016 HELLO ' +  NEUID + '\n'
            strmessage = str(message)
            self.clientSocket.send(strmessage)            
        except:
            print "Unable to send Hello message to the server "
            sys.exit(2)
     
#    Receives a Message from the Server. 
#    Format of the message is: cs5700spring2016 STATUS [a number] [a math operator] [another number]\n
#    The received message can be STATUS, SOLUTION or BYE message
    def receive_Message(self):
        try:
            self.response = self.clientSocket.recv(256)
            if self.response == "":
                print "Unable to receive response from server"
            if "BYE" in self.response:
                global flag
                flag = 0
        except: 
            print "Unable to receive response from server"
            sys.exit(2)
    
#    Strips the received STATUS message, checks if the message is valid.
#    Performs only +, -, /, * operations on the received valid message and calculates results
    def perform_Operation(self):
        splitdata = self.response.split()
        if (splitdata[1] != "STATUS"):
            print "Incorrect message format received"
            sys.exit(2);
            
        splitLength = len(splitdata)
        r = range(1, 1001)
        if (splitLength == 5):
            operator = splitdata[3]
            operand1 = int(splitdata[2])
            operand2 = int(splitdata[4])
            if (operand1 in r and operand2 in r):                
                if operator is "+":
                    self.result = operand1 + operand2       
                elif operator is "-":
                    self.result = operand1 - operand2
                elif operator is "*":
                    self.result = operand1 * operand2            
                elif operator is "/":    
                    self.result = operand1 / operand2  
                else:
                    print "Incorrect STATUS message format received"
                    sys.exit(2) 
            else:
                print "Incorrect STATUS message format received"
                sys.exit(2)                
     
#    Constructs a Solution message and sends the solution to the SERVER
#    Solution Message Format is: cs5700spring2016 [the solution]\n
    def send_Solution(self):
        solutionMessage = "cs5700spring2016 " + str(self.result) + "\n" 
        self.clientSocket.send(solutionMessage)
    
#    This method is executed if the SERVER sends a BYE message.
#    If the provided NEU ID is valid, servers sends a SECRET FLAG. This flag is unique for each NEU ID.
    def get_secret_flag(self):
        splitResponse = self.response.split()
        secret_flag = splitResponse[1]
        
        if "Unknown_Husky_ID" in secret_flag:
            print 'Invalid Husky ID'
        else:
            print secret_flag
        self.clientSocket.close()

#    Main function to execute client-server interactions.
def main():
    clientObj = Client() 
    try:
        clientObj.create_Connection()
        clientObj.send_Hello_Msg()
        while flag == 1:
            clientObj.receive_Message()
            if flag == 1:
                clientObj.perform_Operation()
                clientObj.send_Solution()
        clientObj.get_secret_flag()
    except:
        sys.exit(2)
    

if __name__ == '__main__':
    main()
