import socket
import sys

Host=''                                                               #127.0.0.1

def startProxy(serverAddress, serverPort):
    while True:
	  # 1. Create server socket
      serverSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	  # 2. Bind the server socket to server address and server port
      serverSocket.bind((serverAddress,serverPort))
	  # 3. Continuously listen for connections to server socket
      serverSocket.listen(1)
	  # 4. When a connection is accepted, create a connection socket and get the message
      connectionSocket,addr=serverSocket.accept()
      message=connectionSocket.recv(1024)
      # 5. Get the hostname and transfer it to an ip address
      hostname_1=message.decode().split()[1]
      if hostname_1[0]=='h': hostname=hostname_1.split('/')[2]
      else: hostname=hostname_1.split(':')[0]
      #hostname=(message.decode().split()[1]).split(':')[0]            use browser
      hostaddr=socket.gethostbyname(hostname)
      # 6. Create a new socket to send and message from the client to the host
      newSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
      newSocket.connect((hostaddr,80))
      newSocket.sendall(message)
      # 7. Receive the rely message from the host and send it to the client through connection socket
      data=newSocket.recv(1024)
      connectionSocket.sendall(data)
	  # 8. Close all the socket
      serverSocket.close()
      newSocket.close()
      connectionSocket.close()  
    
Port=int(input("Enter a port number:")) #enter 12000, for the command wget use 12000 as port number.
startProxy(Host, Port)

# wget http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file2.html -e use_proxy=yes -e http_proxy=127.0.0.1:12000  