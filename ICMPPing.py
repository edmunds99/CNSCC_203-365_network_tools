import socket
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0
INITIAL_CHECKSUM=0
DEFAULT_TIMEOUT=2
DEFAULT_ID,DEFAULT_CODE=0,0
UNREACHABLE=3

def checksum(data):
    n = len(data)
    m = n % 2
    sum = 0
    for i in range(0, n - m ,2):
        sum += (data[i]) + ((data[i+1]) << 8)
    if m: sum += (data[-1])
    sum = (sum >> 16) + (sum & 0xffff)
    sum += (sum >> 16)
    answer = ~sum & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def sendOnePing(icmpSocket, destinationAddress, ID, Sequence):
    # 1. Build ICMP header
    send_packet=struct.pack('>BBHHH',ICMP_ECHO_REQUEST,DEFAULT_CODE,INITIAL_CHECKSUM,ID,Sequence)
    # 2. Checksum ICMP packet using given function
    theChecksum=checksum(send_packet)
    # 3. Insert checksum into packet
    send_packet=struct.pack('>BBHHH',ICMP_ECHO_REQUEST,DEFAULT_CODE,theChecksum,ID,Sequence)
    # 4. Send packet using socket
    icmpSocket.sendto(send_packet,(destinationAddress,80))
    #  5. Record time of sending and return
    send_time=time.time()
    return send_time

def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
    # 1. Wait for the socket to receive a reply
    time_start=time.time()
    # 2. Once received, record time of receipt, otherwise, handle a timeout
    readable=select.select([icmpSocket],[],[],timeout)
    if readable[0]==[]: return -1
    receive_time=time.time()
    # 3. Judge whether time out
    if receive_time-time_start>=timeout: return -1
    # 4. Unpack the packet header for useful information, including the ID
    receive_packet,addr=icmpSocket.recvfrom(1024)
    header=receive_packet[20:28]
    r_type, r_code, r_checksum, r_ID, r_seq=struct.unpack(">BBHHH",header)
    # 5. Return the reply time
    if r_ID==ID: return receive_time,r_type

def doOnePing(destinationAddress, Sequence, timeout):
    # 1. Create ICMP socket
    theSocket=socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.getprotobyname("icmp"))
    # 2. Call sendOnePing function
    send_ping_time=sendOnePing(theSocket,destinationAddress,DEFAULT_ID,Sequence)
    # 3. Call receiveOnePing function
    receive_ping_time,reply_type=receiveOnePing(theSocket,destinationAddress,DEFAULT_ID,DEFAULT_TIMEOUT)
    # 4. Close ICMP socket
    theSocket.close()
    # 5. Return total network delay
    return receive_ping_time-send_ping_time,reply_type

def ping(host, timeout,count):
    min_time=1000; max_time=-1; total_time=0; count=0
    # 1. Look up hostname, resolving it to an IP address
    dest=socket.gethostbyname(host)
    print("Ping to",host)
    # 2. Call doOnePing function, approximately every second
    for i in range(0,count_time):
        delay,reply_type=doOnePing(dest,i,DEFAULT_TIMEOUT)
        # 3. Judge whether it is unreachable
        if reply_type==UNREACHABLE:
          print("unreachable")
          return
        if (delay>0):
            count+=1
            print("the reply from ",dest,"time=",int(delay*1000))
            if delay>max_time: max_time=delay
            if delay<min_time: min_time=delay
            total_time+=delay
            time.sleep(1)
        else:
            print("Time out")
    # 4. Print out the returned delay
    ave_time=total_time/count
    print(count,"successfully received, ",count_time-count,"lost")
    print("maximum time is:",int(max_time*1000),"mininum time is:",int(min_time*1000),"average time is:",int(ave_time*1000))

host=input("Enter the host: ")
timeout=int(input("Enter the required timeout: "))
count_time=int(input("Enter the times to measure: "))
ping(host,timeout,count_time)
