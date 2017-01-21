 # -*- coding: utf-8 -*
import socket,select
import sys
import optparse
import threading
import datetime,time
import time
import netifaces as ni
import traceback
import queue
HOST = '192.168.1.104'   # Symbolic name meaning all available interfaces
PORT = 10010        # Arbitrary non-privileged port
sock =  socket.socket


clientList = []
sockList = []
ipList=[]
flag = True
BUFFER = 1024
lock = threading.Lock()  
event = threading.Event()
choose = ""
starttime = 0
endtime = 0


def getLocalEthIps():
    global ipList
    routingNicName = ni.gateways()['default'][ni.AF_INET][1]   #网络适配器信息
    
    for dev in ni.interfaces():
        #print (ni.ifaddresses(dev))
        if dev == routingNicName:
            try:
                routingIPAddr = ni.ifaddresses(dev)[ni.AF_INET][0]['addr']   #获取IP
                #print (routingIPAddr)
            except KeyError:
                pass     
    return routingIPAddr
    
       #  if dev.startswith('eth0'):
        #     ip = ni.ifaddresses(dev)[2][0]['addr']
       #      print (ip)
        
       # if ip not in ipList:
      #      ipList.append(ip)
      #      print ip

class clientInfo(object):
    addr =  ""
    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
    def printData(self):
        print (self.addr)
#----------------------------------------------------------------------
def initServer():
    print ('initServer ')
    
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)   #定义socket类型，网络通信，TCP
        #阻塞与端口复用前后顺序可换  
        sock.setblocking(False)  
        #SOL_SOCKET（套接字描述符）、SO_REUSEADDR（端口复用）  
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        
        rlists=[sock]  
        wlists=[]  
        msg_que={}     
        timeout=10 
    except socket.error  as  msg:
        print ('Failed to create socket. Error code: %s' %msg)
        sys.exit();
    try:
        sock.bind((HOST, PORT))
        
    except socket.error as  msg:
        print ('Bind failed. Error Code : %s' %msg)
        sys.exit()
        print ('Socket bind complete \n' )
    sock.listen(10)
    while True:
        rs,ws,es=select.select(rlists,wlists,rlists,timeout)  
        if not(rs or ws or es):  
            #print 'timeout...' 
            continue         
           #读部分  
        for s in rs:  
        #看s是否是本机上用于监听的socket，是则接受连接，不是则接收数据  
            if s is sock:  
                conn,addr=s.accept()  
                #conn、addr分别是所接收到的socket对象和对方端口 
                client = clientInfo(sock, addr)
                clientList.append(client)
                sockList.append(conn)
                
                print ('connect by %s',addr)  
                conn.setblocking(False)  
                rlists.append(conn)  
                #使用字典将conn与一个队列相对应  
                msg_que[conn]=queue.Queue()              
            else:  
                data = s.recv(1024)  
                if data:  
                    print (data)  
                    msg_que[s].put(data)  
                    if s not in wlists:  
                        wlists.append(s)  
                    else:  
                        if s in wlists:  
                            wlists.remove(s)  
                            rlists.remove(s)  
                            s.close  
                            del msg_que[s]  
        #写部分             
        for  s in ws:  
            try:  
                #get_nowait()跟get(0)一样  
                msg = msg_que[s].get_nowait()  
            except queue.Empty:  
                print ('msg empty \n' )
                wlists.remove(s)  
            else:  
                s.send(msg) 
        for s in es:  
            print ('except',s.getpeername())  
            if s in rlists:  
                rlists.remove(s)  
            if s in wlists:  
                wlists.remove(s)          
        s.close  
#----------------------------------------------------------------------
def process():
    global flag 
    global choose
    global event
    global sockList
    print ('process ')
    
    while(flag):
        while not event.is_set():
            event.wait()  
            time.sleep(1)                 
        if choose == 'list':
            if sockList:
                for item in sockList:
                    print (item)
            else:
                print ("list is null \n" )
        elif choose == 'begin':
            print ("client begin colect  msg \n")
            for item in sockList:
                item.send(choose.encode())
            starttime = datetime.datetime.now()
        elif choose == 'start':
            print ("start all client \n")
        elif choose == 'end':
            print ("client end colect  msg \n")
            for item in sockList:
                item.send(choose.encode())
            endtime = datetime.datetime.now()
            #print "time  last ：s\n"+ (endtime - starttime).seconds
            
            
        elif choose == 'close':
            closeServer()
            flag = False
            print ("end all client \n   " )        
        else:
            print ("no control \n")
            
        event.clear()
    
#----------------------------------------------------------------------
def closeServer():
    print ("closeServer" )     
    sock.close() 


def main():
    global choose    
    HOST = getLocalEthIps()
    print("HOST is %s "%HOST)
    try:
           sthread = threading.Thread(target=initServer) 
           pthread =threading.Thread(target=process) 
           sthread.start()
           pthread.start()
    except:
            traceback.print_exc(file=sys.stdout)
        
    print ("input  your choice ")
    
    while(True):
            choose = input()
            event.set()  
        
if __name__ =='__main__':
    main()
 
 
