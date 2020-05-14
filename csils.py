

import traceback
import serial
import threading
from time import sleep
import subprocess
import msvcrt # needs unix portablility
import json

# terminal line control hack
_=subprocess.call("",shell=True)

# data vars
count = 0
dev1=None
dev2=None
convo_log=[]

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
        "connect":lambda:"1-dev1 2-dev2 a-all c-cancel",
        }
curr_info="help"
curr_mode="main"

#load default conf
conf=json.load(open("conf",'r'))

def updateDisplay():
    global curr_info, curr_mode, convo_log
    #clear
    print("\033[F\033[K"*lines,end="")
    print(info[curr_info]())
    if(curr_mode=="main"):
        for line in convo_log:
            print(line)
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
        while(running):
            for dev in dev1,dev2:
                if dev:
                    msg=dev.readline()
                    if len(msg)>0:
                        convo_log+=[msg]
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

