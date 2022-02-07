import socket
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST=8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY=0    # ICMP type code for echo reply messages
ICMP_TIMEOUT_REPLY=11
UNREACHABLE=3
CODE, ID, SEQ=0, 0, 1
INITIAL_CHECKSUM=0
MEASURE_TIME=3
DEFAULT_HOPS=30

def checksum(data):
    n = len(data)
    m = n % 2
    sum = 0
    for i in range(0, n - m, 2):
        sum += (data[i]) + ((data[i + 1]) << 8)
    if m: sum += (data[-1])
    sum = (sum >> 16) + (sum & 0xffff)
    sum += (sum >> 16)
    answer = ~sum & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer
    
def gethostname(host_addr):
    try:
      hostname=socket.gethostbyaddr(host_addr)
    # 1. throw an exception, no correspond hostname
    except socket.error as e:
      result=('{0} (no host name)'.format(host_addr))
    else:
      result=('{0} ({1})'.format(host_addr, hostname[0]))
    return result

def receiveOnePing(icmpSocket, destinationAddress, timeout):
    # 1. Wait for the socket to receive a reply
    time_s=time.time()
    readable=select.select([icmpSocket], [], [], timeout)
    # 2. Once received, record time of receipt, otherwise, handle a timeout
    if readable[0] == []: return -1
    receive_time=time.time()
    if receive_time - time_s >= timeout: return -1
    # 3. Return the time of receiving and return
    return receive_time

def sendOnePing(icmpSocket, destinationAddress):
    # 1. Build ICMP header
    send_packet=struct.pack(">BBHHH", ICMP_ECHO_REQUEST, CODE, INITIAL_CHECKSUM, ID, SEQ)  
    # 2. Checksum ICMP packet using given function
    the_Checksum=checksum(send_packet)
    # 3. Insert checksum into packet
    send_packet=struct.pack(">BBHHH", ICMP_ECHO_REQUEST, CODE, the_Checksum, ID, SEQ)
    # 4. Send packet using socket
    icmpSocket.sendto(send_packet, (destinationAddress, 0))
    #  5. Record time of sending and return
    send_time=time.time()
    return send_time

def doOnePing(destinationAddress, timeout, ttl, prototype):
    # 1. Create ICMP socket
    if prototype=="icmp":
      theSocket=socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname(prototype))
    theSocket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))          
    # 2. Call sendOnePing function
    send_ping_time=sendOnePing(theSocket, destinationAddress)
    # 3. Call receiveOnePing function and calculate the delay
    receive_ping_time=receiveOnePing(theSocket, destinationAddress, timeout)
    delay = receive_ping_time - send_ping_time
    if (delay<0): return -1, -1, -1
    # 4. get the information of the socket and close it
    receive_packet, router=theSocket.recvfrom(1024)
    header=receive_packet[20:28]
    router_address=router[0]
    reply_type, reply_code, reply_checksum, reply_id, reply_sequence=struct.unpack(">BBHHH", header)
    theSocket.close()
    # 5. Return total network delay,router address and reply type
    return delay, router_address, reply_type

def traceroute(host, timeout, prototype):
    # 1. Look up hostname, resolving it to an IP address
    dest= socket.gethostbyname(host)
    # 2. Increase the ttl, call doOnePing function, approximately every second
    for ttl in range(1, DEFAULT_HOPS):
      flag=0
      print(ttl,end="  ")
      for i in range(0,MEASURE_TIME):
        delay, router_add, reply_type=doOnePing(dest, timeout, ttl,prototype)
        # 3. Print out the result according to the reply code
        if delay<0:
          print("*",end="  ")
          continue
        flag=1
        router_address=router_add
        if reply_type==ICMP_ECHO_REPLY:
          print(int(delay*1000),end="  ")
        elif reply_type==ICMP_TIMEOUT_REPLY:
          print(int(delay*1000),end="  ")
          continue
        elif reply_type==UNREACHABLE:
          print("unreachable",end="  ")
      if flag==0: print("timeout")
      elif reply_type==ICMP_ECHO_REPLY:
        print(gethostname(router_address))
        print("Reach the destination")
        return
      elif reply_type==UNREACHABLE:
        print("Unreachable node")
        return 
      else: print(gethostname(router_address))

host=input("Enter the host: ")
timeout=int(input("Enter the required timeout: "))
prototype="icmp"
print("Getting the route to host",host)
traceroute(host, timeout, prototype)

#  C:\Users\HP\Desktop\school\cs\networks\coursework
