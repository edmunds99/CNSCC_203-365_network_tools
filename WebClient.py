#P111 from top to down
from socket import *

serverAddress='127.0.0.1'

# 1.create a client socket
clientSocket=socket(AF_INET,SOCK_STREAM)
# 2.input a port (same as the one in WebServer.py) and connect
serverPort=int(input("Enter the corresponding port number:"))
clientSocket.connect((serverAddress,serverPort))
# 3.create the http GET message
data="GET /index.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n"
# 4.send the http get message
clientSocket.send(data.encode())
# 5.get the received message and print
received_data=clientSocket.recv(1024)
while received_data:                                        #
  print(received_data.decode())
  received_data=clientSocket.recv(1024)
# 6.close the client socket
clientSocket.close()
