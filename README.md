
# Botnet

## Basics
This program, written in Python, utilizes sockets to create a botnet. A botnet is a group of computers that do the work of a central computer known as command and control. This particular botnet is implemented such that the command and control can send three different things (RUN, STOP, REPORT) and then a python script for it to perform the operation on. The operation is then performed by the zombies in the botnet. RUN is implemented to start running a script. STOP is implemented to stop a script if it is currently running. REPORT is implemented to report the status of the script.

## Implementation
To implement the botnet, I started with the server (The point that recieves requests and performs them) and the hosts (The point that sends the requests). This is an application level program that utilizes TCP to send packets between computers.

## Tools Utilized

        -> Python
        -> Git
        -> GitHub


## Author

- [@25cdickerson](https://www.github.com/25cdickerson)

