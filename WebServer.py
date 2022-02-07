import socket
import sys
import threading

Host=''                                                             #127.0.0.1

def handleRequest(tcpSocket):
	# 1. Receive request message from the client on connection socket
    message=tcpSocket.recv(1024)
	# 2. Extract the path of the requested object from the message (second part of the HTTP header)
    filename=message.split()[1]                                     
	# 3. Read the corresponding file from disk
    try: 
      f=open(filename[1:],"rb")                                     #if not exist in the same directory, throw an exception                            
	  # 4. Store in temporary buffer
      file=f.read().decode()
	  # 5. Send the HTTP response 200 OK
      http_response="HTTP/1.1 200 OK\r\n\r\n"                       #200 OK (the format)
      tcpSocket.send(http_response.encode())
	  # 6. Send the content of the file to the socket
      tcpSocket.send(file.encode())
	  # 7. Close the connection socket
      tcpSocket.close()     
    # 8.Not exist in the same directory, throw an exception 
    except IOError:
      # 9.Send the HTTP response 404 Not Found
      http_response="HTTP/1.1 404 Not Found\r\n\r\n"                #404 Not Found (the format)
      tcpSocket.send(http_response.encode())
      tcpSocket.close()      

def startServer(serverAddress, serverPort):
	# 1. Create server socket
    serverSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	# 2. Bind the server socket to server address and server port
    serverSocket.bind((serverAddress,serverPort))
	# 3. Continuously listen for connections to server socket
    serverSocket.listen(5)
	# 4. When a connection is accepted, call handleRequest function, passing new connection socket
    while True:
      connectionSocket,addr=serverSocket.accept()                   #blocked until receiving a message
      # 5. Create a new thread
      newThread=threading.Thread(target=handleRequest,args=(connectionSocket, ))             
      newThread.start()
	# 6. Close server socket
    serverSocket.close()

Port=int(input("Enter a port number:"))
startServer(Host, Port)
