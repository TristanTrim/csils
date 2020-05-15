
import serial

import traceback
import threading
from time import sleep, time
import subprocess
try:
    import msvcrt # windows
    OS = "windows"
    def getch():
        return(msvcrt.getch().decode("utf-8"))
except ModuleNotFoundError:
    # linux
    OS = "linux"
    import sys, tty, termios
    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

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
    print("\r",end="")
    if(curr_mode=="main" or curr_mode=="tags"):
        for ii in range(log_offset,min(log_offset+lines-1,len(convo_log))):
            line = convo_log[ii]
            if ii == main_curr:
                print("\033[1;37m",end="")#white
            else:
                print("\033[0;37m",end="")#grey
            #[ time, source, msg, tags ]
                    # line number
                    # msg time\
                    # device name\
                    # hex msg\
                    # tags\
            outputLine="%4d"%ii \
                    +" %6dms "%(line[0]*1000)\
                    +"%4s:"%line[1] \
                    +"%-20s"%line[2] \
                    +"... "\
                    +"%8s"%line[3] \
                    +"\r"
            print(outputLine[:columns])
        print("\033[0;37m\r",end="")#grey
        for ii in range(lines-1-len(convo_log)):
            print("...\r")
    elif(curr_mode=="config"):
        print(" ",conf["dev1"],"\r")
        print(" ",conf["dev2"],"\r")
        for ii in range(lines-1-2):
            print("%8d"%count,"foo","\r")

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
    global log_offset,main_curr
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
                                tags[:]]
                        logfile=open(conf["log"],'a+')
                        json.dump(new_msg,logfile)
                        logfile.write('\n')
                        logfile.close()
                        convo_log+=[new_msg]
                        if(main_curr==len(convo_log)-2):
                            main_curr+=1
                            log_offset+=1

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
    gg=False
    while(running):
        inp=getch()
        if(inp=="q"):
            running=False
        elif(inp=="m"):
            curr_info="main"
            curr_mode="main"
        elif curr_mode=="main":
            ### motion controls ###
            ## gg latch ##
            if(inp=="g"):
                if(gg):
                    main_curr=0
                    log_offset=0
                else:
                    gg=True
            else:
                gg=False
            ## other stuff ##
            if(inp=="j"):
                main_curr+=1
                if(main_curr==len(convo_log)):
                    main_curr=len(convo_log)-1
                elif(main_curr>log_offset+lines-2):
                    log_offset+=1
            elif(inp=="k"):
                main_curr-=1
                if(main_curr==-1):
                    main_curr=0
                elif(main_curr<log_offset):
                    log_offset-=1
            elif(inp=="G"):
                main_curr=len(convo_log)-1
                log_offset=len(convo_log)-lines+1
            ### other main stuff ###
            elif(inp=="c"):
                curr_info="config"
                curr_mode="config"
            elif(inp=="t"):
                curr_mode="tags"
                curr_info="tags"
        elif curr_mode=="config":
            if(inp=="c"):
                prev_info=curr_info
                curr_info="connect"
                inp=getch()
                if(inp=="1"):
                    dev1=serial.Serial( *conf["dev1"][1], timeout=0)
                elif(inp=="2"):
                    dev1=serial.Serial( *conf["dev2"][1], timeout=0)
                elif(inp=="a"):
                    dev1=serial.Serial( *conf["dev1"][1], timeout=0)
                    dev1=serial.Serial( *conf["dev2"][1], timeout=0)
                curr_info=prev_info
            elif(inp=="n"):
                pass
            elif(inp=="p"):
                pass
            elif(inp=="b"):
                pass
        elif curr_mode=="tags":
            if(inp=="n"):
                curr_info="newtag"
                entry_buf=""
                while True:
                    inp=getch()
                    if(inp=="\r"):#enter
                        tags+=[entry_buf]
                        curr_mode=curr_info="main"
                        break
                    # windows and linux seem to have diff backspace?
                    # or is it my keyboard?
                    # anyway:  windows        linux
                    elif(inp=="\x08" or inp=="\x7f"):#backspace
                        entry_buf=entry_buf[:-1]
                    else:
                        entry_buf+=inp
except Exception:
    print(traceback.format_exc())
    running=False

#default white text...
print("\033[1;37m",end="")
