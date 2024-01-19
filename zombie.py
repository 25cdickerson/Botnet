#####################################
# Zombie controlled by the          #
# command and control               #
#                                   #
#                                   #
# Preston Dickerson                 #
#                                   #
#####################################


# Function that buffers the request from the command and control

import select
import socket
import sys


def bufferRequest(connectionSocket, exitFlag):
    finalBuffer = ""
    # run the loop until no buffers are left or the carriage return new line character sequence is found
    while True:
        if exitFlag.is_set():
            connectionSocket.close()
            break

        # Get 1024 bytes of information
        buffer = connectionSocket.recv(1024).decode()
        if not buffer:
            break
        finalBuffer += buffer
        if '\r\n\r\n' in finalBuffer:
            break  # Break the loop when the end of the request headers is reached
    
    return finalBuffer

def main():
        # Get the command for what we are connecting to, throw an error if there is not command line argument
    if len(sys.argv) < 2:
        print("Please enter arguments like this: ./myserver.py <Port1> <Port2> <Port3>.")
        return
    
    # Setup the server sockets
    serverSockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(len(sys.argv)-1)]
    for i, serverSocket in enumerate(serverSockets):
        # Get the server port
        serverPort = int(sys.argv[i+1])
        
        # Set the SO_REUSEADDR option to allow reuse of the address (Want this for after termination)
        serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind to the server port
        serverSocket.bind(('', serverPort))

        # Listen at that server port
        serverSocket.listen(3)
        print(f"Server is listening at Port {serverPort}")

        # Use select to keep track of all server sockets
        while True:
            read, _, _ = select.select(serverSockets, [], [], 5)  # '5' for non-blocking
            for s in read:
                #connectionSocket, addr = s.accept()
                print("connection")

main()