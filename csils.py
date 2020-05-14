
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
display_rate = .2
convo_rate = .01
running = True
default_conf_file = "conf"

#menu vars
info={
        "help":lambda:"q-quit(global) c-config",
        "config":lambda:"c-connect n-name p-port b-baud m-main",
        "conf":lambda:str(conf),
        "connect":lambda:"1-{} 2-{} a-all c-cancel".format(
                        conf["dev1"][0], conf["dev2"][0]),
        }
curr_info="help"
curr_mode="main"

#load default conf
conf=json.load(open("conf",'r'))
#load log
convo_log=[]
logfile=open(conf["log"],'r+')
for line in logfile:
    convo_log+=[json.loads(line)]
logfile.close()

def updateDisplay():
    global curr_info, curr_mode, convo_log
    #clear
    print("\033[F\033[K"*lines,end="")
    print(info[curr_info]())
    if(curr_mode=="main"):
        for ii,line in enumerate(convo_log):
            if ii == 1:
                print("\033[1;37m",end="")#white
            else:
                print("\033[0;37m",end="")#grey
            outputLine=str(line)
            print(outputLine[:columns])
        print("\033[0;37m",end="")#grey
        for ii in range(lines-1-len(convo_log)):
            print("%8d"%count,"foo")
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
    global running, count, convo_log
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
        elif curr_mode=="main":
            if(inp==b"c"):
                curr_info="config"
                curr_mode="config"
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
            elif(inp==b"m"):
                curr_info="help"
                curr_mode="main"
except Exception:
    print(traceback.format_exc())
    running=False

#default white text...
print("\033[1;37m",end="")
