#---------------------------------------------------------------------------
# cam_server
# -- a python service to accept wifi-cam connection and capture image from wifi-cam
#
# BSD 3-clause license is applied to this code
# Copyright(c) 2015 by Aixi Wang <aixi.wang@hotmail.com>
#---------------------------------------------------------------------------
#!/usr/bin/python

import socket
import threading               # Import socket module
import time
import os,sys
from tcpcam2cloud import *

jpg_bin = ''
status = 0
#socket.setdefaulttimeout(1)
ALL_CLIENT = []
GRANT_MAC_LIST = ['\xac\xcf\x23\x52\xbb\x94','\xff\xff\xff\xff\xff\xff']
CAPTURE_INTERVAL = 3600
BASE_FOLDER = '/usr/share/nginx/www/img/'
#BASE_FOLDER = ''



#-------------------
# writefile2
#-------------------
def writefile2(filename,content):
    f = file(filename,'ab')
    fs = f.write(content)
    f.close()
    return 
    
# Define tcp handler for a thread...
def myHandler(client, addr):
    global ALL_CLIENT
    global jpg_bin
    global BASE_FOLDER
    global status
    
    mac_addr = ''
    client.setblocking(0)

    ALL_CLIENT.append({
        'fd': client,
        'addr': addr,
        'closed': False
    });

    print 'thread started for ', addr
    data=''
    jpg_bin = ''
    c1 = ''
    while True:
        # avoid cpu loading too hight
        time.sleep(1)
        try:
            msg = client.recv(1024*64)
            mac_addr = msg[0:6].encode('hex')
            print 'macaddr:',mac_addr
            c1 += msg[6:]
            
        except socket.error as e:
            if c1 != '':
                #print 'recv %d bytes' % (len(c1
                # recognize jpg header & tail            === start
                i = c1.find('\xff\xd8')
                if  i>= 0:
                    jpg_bin = c1[i:]
                    status = 1
                    print '[JPG'
                    #continue

                    j = jpg_bin.find('\xff\xd9')                        
                    if j > 0:
                        print '--JPG]'                        
                        jpg_bin = jpg_bin[:j+2]
                        s = BASE_FOLDER + mac_addr + '#' + filename_from_time()
                        print s
                        writefile(s,jpg_bin)
                        jpg_bin = ''
                        c1 = ''

                        time.sleep(CAPTURE_INTERVAL)                        
                        client.close()
                        break
                        
                    
                j = c1.find('\xff\xd9')                        
                if j >= 0:
                    if status == 1:
                        print 'JPG]'                        
                        jpg_bin += c1[:j+2]
                        s = BASE_FOLDER + mac_addr + '#' + filename_from_time()
                        print s
                        writefile(s,jpg_bin)
                        jpg_bin = ''
                        c1 = ''
                        
                        time.sleep(CAPTURE_INTERVAL)
                        client.close()
                        break
                        
                else:
                    if status == 1:
                        jpg_bin += c1

                # recognize jpg header & tail            === end
                
            continue
        except Exception as e:
            print 'Server get a error fd: ', e
            client.close()            
            break


#----------------------
# main
#----------------------
if __name__ == "__main__":
    # To launch Socket Server
    
    while True:
        try:
            server = socket.socket()
            host = socket.gethostname()
            port = 8899
            server.bind(('', port))
            server.listen(5)
            print 'Server FD No: ', server.fileno()
            break
            
        except:
            time.sleep(3)
    
    while True:
        try:
            client, addr = server.accept()
            print 'Got connection from', addr, ' time:', format_time_from_linuxtime(time.time())
            #header = client.recv(32)
            #h_s = header.encode('hex')
            #print 'header:', h_s
            s = 'new connection from %s, time: %s\r\n' % (str(addr),str(format_time_from_linuxtime(time.time())))
            writefile2('log.txt',s)
            
            #if (header in GRANT_MAC_LIST):
            #    print 'new thread created! for addr:',addr
            module_reset(client)
            time.sleep(1)
            module_snapshot(client)
            time.sleep(0.5)
            module_read_pic_data2(client,32000)
                             
            threading.Thread(target=myHandler, args=(client, addr)).start()
            
        except:
            print 'except, try again.'
            time.sleep(3)

