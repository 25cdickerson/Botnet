#####################################
# Client that controls the zombies  #
# in botnet                         #
#                                   #
#                                   #
# Preston Dickerson                 #
#                                   #
#####################################


# Object that deals with the buffering of http responses
import socket


class Buffer(object):
    def __init__(self):
        self.buf = ""

    def bufferMessages(self, sock):
        # Parse into buffer
        while True:
            chunk = sock.recv(1024).decode()
            if not chunk:
                break
            self.buf += chunk

    def getBuffer(self):
        return self.buf
    
def main():
    # Get input

    # Define the socket
    sock = socket(socket.AF_INET, socket.SOCK_STREAM)

    #sock.connect((hostname, port))