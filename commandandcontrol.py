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

    # Iterate through the IP-port dictionary
    for ip, ports in ipDictionary.items():
        for port in ports:
            # Define the socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Connect to each IP and port
            try:
                sock.connect((ip, int(port)))
                print(f"Connected to {ip}:{port}")
            except Exception as e:
                print(f"Failed to connect to {ip}:{port}. Error: {e}")
            finally:
                # Close the socket after connecting or failing to connect
                sock.close()

main()