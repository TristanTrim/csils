
import serial

import traceback
import threading
from time import sleep, time
import subprocess
import msvcrt # needs unix portablility
import json

# get the size of the terminal
import os
rows, columns = (int(x) for x in os.popen('stty size', 'r').read().split())

# terminal line control hack
_=subprocess.call("",shell=True)

# data vars
count = 0
dev1=None
dev2=None

# config vars
lines = 13
print("\n"*lines)
display_rate = .05
convo_rate = .01
running = True
default_conf_file = "conf"
main_curr=0
log_offset=0
entry_buf=""
tags=[]

#menu vars
info={
        "main":lambda:"q-quit(global) c-config t-tags  %8d"%count,
        "config":lambda:"c-connect n-name p-port b-baud m-main",
        "conf":lambda:str(conf),
        "connect":lambda:"1-{} 2-{} a-all c-cancel".format(
                        conf["dev1"][0], conf["dev2"][0]),
        "tags":lambda:"n-new d-delete",
        "newtag":lambda:entry_buf,
        }
curr_info="main"
curr_mode="main"

#load default conf
conf=json.load(open("conf",'r'))
#load log
convo_log=[]
logfile=open(conf["log"],'r+')
for line in logfile:
    convo_log+=[json.loads(line)]
logfile.close()

#############
## Display ##
#############
def updateDisplay():
    global curr_info, curr_mode, convo_log, main_curr
    #clear
    print("\033[F\033[K"*lines,end="")
    print(info[curr_info]())
    if(curr_mode=="main" or curr_mode=="tags"):
        for ii in range(log_offset,log_offset+lines-1):
            line = convo_log[ii]
            if ii == main_curr:
                print("\033[1;37m",end="")#white
            else:
                print("\033[0;37m",end="")#grey
            # time, source, msg, tags
            outputLine="%4d"%ii\
                    +" %6dms "%(line[0]*1000)\
                    +"%4s:"%line[1]\
                    +"%20s"%line[2]\
                    +"... "\
                    +"%8s"%line[3]
            print(outputLine[:columns])
        print("\033[0;37m",end="")#grey
        for ii in range(lines-1-len(convo_log)):
            print("...")
    elif(curr_mode=="config"):
        print(" ",conf["dev1"])
        print(" ",conf["dev2"])
        for ii in range(lines-1-2):
            print("%8d"%count,"foo")

def displayLoop():
    global running
    try:
        while running:
            updateDisplay()
            sleep(display_rate)
    except Exception:
        print(traceback.format_exc())
        running=False

displayThread = threading.Thread(target=displayLoop)
displayThread.start()

###########
## Convo ##
###########
def convoLoop():
    global running, count, convo_log, tags
    try:
        tags=['unknown']
        lastTime=time()
        while(running):
            for dev in dev1,dev2:
                if dev:
                    msg=dev.readline()
                    if len(msg)>0:
                        thisTime=time()
                        deltaTime=thisTime-lastTime
                        lastTime=thisTime
                        new_msg=[
                                deltaTime,
                                dev.name,
                                msg.hex(),
                                tags]
                        logfile=open(conf["log"],'a+')
                        json.dump(new_msg,logfile)
                        logfile.write('\n')
                        logfile.close()
                        convo_log+=[new_msg]
                            # too nested
            count+=1
            sleep(convo_rate)
    except Exception:
        print(traceback.format_exc())
        running=False
convoThread = threading.Thread(target=convoLoop)
convoThread.start()

#UI loop
try:
    while(running):
        inp=msvcrt.getch()
        if(inp==b"q"):
            running=False
        elif(inp==b"m"):
            curr_info="main"
            curr_mode="main"
        elif curr_mode=="main":
            if(inp==b"c"):
                curr_info="config"
                curr_mode="config"
            elif(inp==b"j"):
                main_curr+=1
                if(main_curr==len(convo_log)):
                    main_curr=len(convo_log)-1
                elif(main_curr>log_offset+lines-2):
                    log_offset+=1
            elif(inp==b"k"):
                main_curr-=1
                if(main_curr==-1):
                    main_curr=0
                elif(main_curr<log_offset):
                    log_offset-=1
            elif(inp==b"t"):
                curr_mode="tags"
                curr_info="tags"
        elif curr_mode=="config":
            if(inp==b"c"):
                prev_info=curr_info
                curr_info="connect"
                inp=msvcrt.getch()
                if(inp==b"1"):
                    dev1=serial.Serial( *conf["dev1"][1], timeout=0)
                elif(inp==b"2"):
                    dev1=serial.Serial( *conf["dev2"][1], timeout=0)
                elif(inp==b"a"):
                    dev1=serial.Serial( *conf["dev1"][1], timeout=0)
                    dev1=serial.Serial( *conf["dev2"][1], timeout=0)
                curr_info=prev_info
            elif(inp==b"n"):
                pass
            elif(inp==b"p"):
                pass
            elif(inp==b"b"):
                pass
        elif curr_mode=="tags":
            if(inp==b"n"):
                curr_info="newtag"
                entry_buf=""
                while True:
                    inp=msvcrt.getch()
                    if(inp==b"\r"):#enter
                        tags+=[entry_buf]
                        curr_mode=curr_info="main"
                        break
                    elif(inp==b"\x08"):#backspace
                        entry_buf=entry_buf[:-1]
                    else:
                        entry_buf+=inp.decode("utf-8")
except Exception:
    print(traceback.format_exc())
    running=False

#default white text...
print("\033[1;37m",end="")
