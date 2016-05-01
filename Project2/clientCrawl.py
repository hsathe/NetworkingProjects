'''
Created on Feb 2, 2016

@author: Kaustubh Pande, Harshad Sathe
'''
# Import packages to support socket, Regular Expression, BeautifulSoup and Sets

import socket
import re
from bs4 import BeautifulSoup
import sys
from sets import Set
#import time
#import traceback

class FakebookCrawler:

#   Default constructor of a class FakebookCrawler which initializes 
#   Hostname, Port Number, and lists frontier and visited to store
#   discovered and  visited URLs respectively. secretFlags is the
#   set holding all the discovered flags. It also initializes the username
#   and the password from command line
    
    def __init__(self):
        commandLine = sys.argv
        self.host = "cs5700sp16.ccs.neu.edu"
        #self.username = "001941507"
        #self.password = "STOX8SC5"
        self.username = str(commandLine[1])    #"001715861"
        self.password = str(commandLine[2])    #"ZUOTVB0E"
        self.PORTNUM = 80
        self.frontier = []
        self.visited = []
        self.secretFlags = set([])
        

#    This method creates the socket connection by passing Hostname and Port Number
    
    def create_Connection(self):
        self.tcpsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpsoc.connect((self.host, self.PORTNUM))


#    This method handles two responses. First, it gets the login page by sending GET request to the 
#    server. It then parses the response received to retrieve session ID and csrf token. Second, it 
#    sends the POST request to the server with the username, password, csrf token as the post Body 
#    and all other headers.
      
    def login(self):
        self.tcpsoc.sendall("GET /accounts/login/?next=/fakebook/ HTTP/1.1\r\nHost: {0}\r\n\n".format(self.host))
        response = self.tcpsoc.recv(4096)
        try:
            session_pattern = re.compile(r'sessionid=([a-z0-9]+);')
            self.session = session_pattern.findall(response)[0]
            csrf_pattern = re.compile(r'csrftoken=([a-z0-9]+);')
            self.csrftoken = csrf_pattern.findall(response)[0]
            postBody = 'csrfmiddlewaretoken={0}&username={1}&password={2}&next='.format(self.csrftoken, self.username, self.password)
            request = 'POST /accounts/login/ HTTP/1.1\r\nHost: {0}\r\nConnection: keep-alive\r\nContent-Length: {1}\r\nContent-Type: application/x-www-form-urlencoded\r\nCookie: csrftoken={2}; sessionid={3}\r\n\r\n{4}'.format(self.host, len(postBody), self.csrftoken, self.session, postBody)
            self.tcpsoc.sendall(request)
            result = self.tcpsoc.recv(4096)
            self.handle_login(result)
        except IndexError:
            self.create_Connection()
            self.login()
            

#    This method handles the case of receiving 302. If the response code is 302, i.e. 
#    if the page is moved temporarily, the response gives new location. Method first updates
#    the session variable with the new one and splits the headerlist to get new location.
#    It also appends the new location in the frontier list.

    def handle_login(self, result):
        self.get_SessionID(result)
        try:
            headerList = result.split("\n")
            statusCode = int(headerList[0].split(" ")[1])
            if(statusCode == 302):
                redirectURL = self.getNextURL(headerList)
                self.frontier.append(redirectURL)
            elif (statusCode == 200):
               	#print "in 200"
                soup = BeautifulSoup(result, "html.parser")
                r1 = soup.find('ul', {'class' :'errorlist'})
                if r1:
                    sys.exit("Invalid login credentials")
                
                redirectURL = '/fakebook/'
                self.frontier.insert(0, redirectURL)
            else:
                self.create_Connection()
                self.login()
        except:
            print "Invalid Login Credentials"
                
            #traceback.print_exc()
        

#    This method contains the core logic of crawling. It first pops the first URL 
#    out of frontier. Then, the GET request is placed through another method to receive 
#    a response from server. Then, checks the status code of response received.  
#    Response is treated differently depending on status code. This continues
#    until either the 5 secret flags are discovered or frontier becomes empty.  


    def beginCrawling(self):
        
        while (len(self.secretFlags) < 5 and len(self.frontier) > 0):
            basePage = self.frontier.pop(0)
	#    print "Basepage " + str(basePage)
            self.openLink(basePage)             # Pass the popped URL to the method to get response
            statusCode = self.getStatusCode(self.response)      # Get the status code

            if (statusCode == 200):
                self.get_Links()                           # If status code is 200, get all the links in the page
                self.visited.append(basePage)              # Mark the URL as visited 
            elif (statusCode == 301 or statusCode == 302):              # If the status code is 301 or 302, insert the new
                self.frontier.insert(0, self.getNextURL(self.response)) # URL returned by the response into the frontier
            elif (statusCode == 403 or statusCode == 404):          # If status code is 403 or 404, abandon URL
                self.visited.append(basePage)                       # by marking it visited
            elif (statusCode == 500):                               # Is status code is 500, recreate the connection
                self.create_Connection()                            # and retry the link by inserting it at first position
                self.frontier.insert(0, basePage)
            else:
                self.create_Connection()                            # This executes when response received does not contain
                self.frontier.insert(0, basePage)                   # status code, client tries to get response again.

        for flag in self.secretFlags:
            print flag
        self.tcpsoc.close()
    
#    This method finds all the links from the given page. It uses Regular
#    Expression to match links on a page. For each newly discovered URL,
#    it checks if the URL is already visited, if it is, it won't add it again 
#    in the frontier. In the other case, however, link is added into the frontier.
    
    
    def get_Links(self):
        
        link_pattern = re.compile(r'<a href="([a-z0-9/]+)">')
        links = link_pattern.findall(self.response)
        
        for link in links:
            if (link not in self.visited and link not in self.frontier):
                self.frontier.append(link)

        self.get_SecretFlag(self.response)                  # Search for Secret flag in the response
    
    
#    This method returns the status code from the given response.
#    It splits the given HTML response to find out the status code or returns -1 if 
#    response doesn't contain status code

   
    def getStatusCode(self, currentPage):
	#print "current Page " + str(currentPage)
        try:
            headerList = currentPage.split("\n")
            statusCode = int(headerList[0].split(" ")[1])
            return int(statusCode)
        except:
            return -1


#    This method places the GET request for given URL. This URL is typically the 
#    first element popped out of frontier

    def openLink(self, new_link):

        self.request = 'GET {0} HTTP/1.1\r\nHost: {1}\r\nConnection: keep-alive\r\nCookie: csrftoken={2};sessionid={3}\r\n\r\n'.format(new_link, self.host, self.csrftoken, self.session)
        self.tcpsoc.sendall(self.request)
        self.response = self.tcpsoc.recv(4096)


#    This method searches for the secret flags in a given page. The method is called
#    for every page. If the page contains any <h2> tag with 'secret_flag' class name,
#    those flags are added into the set of secret flags. Beautiful Soup is used to parse
#    the responses.

    def get_SecretFlag(self, currentPage):
        try:
            soup = BeautifulSoup(currentPage, "html.parser")
            result = soup.find('h2', {'class' :'secret_flag'})
            if result:
                flag = str(result.text)
                self.secretFlags.add(flag.split(": ")[1])
               # print str(len(self.secretFlags)) + "length of secret flag "
        except:
            print "Exception in secret flags"

#    This method is called when status code of the response is either
#    301 or 302. These are 'Moved Permanently' and 'Moved Temporarily' 
#    responses respectively. In that case, this method parses the response 
#    to find out the new location returned by the server.
                    
     
    def getNextURL(self,headerList):
        for i, s in enumerate(headerList):
            if "Location" in s:
                location = headerList[i]        
        locationSplit = location.split(" ")
        location = locationSplit[1]
        return location

#    This method updates the session ID by parsing the response
#    from server.

    def get_SessionID(self, response):
        session_pattern = re.compile(r'sessionid=([a-z0-9]+);')
        self.session = session_pattern.findall(response)[0]


#    This method updates the CSRF token by parsing the response
#    from server.
   
    def get_CSRFToken(self):
        csrf_pattern = re.compile(r'csrftoken=([a-z0-9]+);')
        self.csrftoken = csrf_pattern.findall(self.response)[0]
 
#    Main method calls all the required methods to kickstart crawling of 
#    fakebook.
    
def main():
    
    if(len(sys.argv) == 3):
        crawlObj = FakebookCrawler()
        crawlObj.create_Connection()
        crawlObj.login()
        crawlObj.beginCrawling()
    else:
        sys.exit("Invalid Number of Args")

if __name__ == '__main__':
   # start_time = time.time()
    main()
   # print("--- %s seconds ---" % round(time.time() - start_time, 2))
