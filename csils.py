
import serial

import traceback
import threading
from time import sleep, time
import subprocess

import parsetree

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

def debug(msg):
    fl=open("debug","a+")
    fl.write(str(msg))
    fl.write("\n")
    fl.flush()
    fl.close()
# get the size of the terminal
import os
rows, columns = (int(x) for x in os.popen('stty size', 'r').read().split())

# terminal line control hack
_=subprocess.call("",shell=True)

# data vars
count = 0

# config vars
lines = rows-3#13
print("\n"*lines)
display_rate = .05
convo_rate = .01
running = True
default_conf_file = "conf"
main_curr=0
log_offset=0
entry_buf=""
tags=[]
tree_curr=0
tree_curr_h=0
tree_offset=0

#menu vars
info={
        "main":lambda:"q-quit(global) c-config t-tags  %8d"%count,
        "config":lambda:"c-connect d-disconnect n-name p-port b-baud m-main",
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

com1=None
com2=None
dev1=parsetree.Root(conf["dev1"][0],None,None)
dev2=parsetree.Root(conf["dev2"][0],None,None)

parseTree = None
parseTreeLock = True

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
    global tree_curr,tree_offset,tree_curr_h
    #go to top
    print("\033[F"*lines,end="")
    print("\033[K",end="")
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
            print("\033[K",end="")
            print(outputLine[:columns])
        print("\033[0;37m\r",end="")#grey
        for ii in range(lines-1-len(convo_log)):
            print("\033[K",end="")
            print("...\r")
    # print config screen
    elif(curr_mode=="config"):
        for dev,devstr in (dev1,"dev1"),(dev2,"dev2"):
            print("\033[K",end="")
            print(str(dev)[:columns],"\r")
            print("\033[K",end="")
            print(("getsFrom: "+str(dev.getsFrom))[:columns-1],"\r")
            print(("sendsTo: "+str(dev.sendsTo))[:columns-1],"\r")
            print("\033[K",end="")
            print(" ",conf[devstr],"\r")
        #TODO: this might break if < 6 lines??? not that anyone should try to use the program like that.
        for ii in range(lines-1-8):
            print("\033[K",end="")
            print("%8d"%count,"foo","\r")
    # print parse tree screen
    elif(curr_mode=="parseTree"):
        if not parseTreeLock:
            debug("tree_offset"+str(tree_offset))
            debug("len(parseTree):"+str(len(parseTree)))
            for ii in range(tree_offset,min(tree_offset+lines-1,len(parseTree))):
                debug("index: "+str(ii))
                line = parseTree[ii]
                outputLine="%4d"%ii \
                        +" "
                for jj,node in enumerate(line):
                    if ii == tree_curr and jj == tree_curr_h:
                        outputLine+="\033[1;37m"#white
                    else:
                        outputLine+="\033[0;37m"#grey
                    outputLine+="|"+node
                outputLine=outputLine[:columns-3]\
                        +"\033[K\r"
                print(outputLine)
            print("\033[0;37m\r",end="")#grey
            for ii in range(lines-1-len(parseTree)):
                print("\033[K",end="")
                print("...\r")
        else:
            for ii in range(lines-1):
                print("\033[B\r",end="")

def displayLoop():
    try:# everything is in try loop so thread can be stopped
        global running
        while running:
            updateDisplay()
            sleep(display_rate)
    except Exception:
        # traceback
        print(traceback.format_exc(),end="\n\r")
        running=False

displayThread = threading.Thread(target=displayLoop)
displayThread.start()

###########
## Convo ##
###########
def convoLoop():
    try:# everything is in try loop so thread can be stopped
        global running, count, convo_log, tags
        global log_offset,main_curr
        global tree_offset,tree_curr,tree_curr_h,parseTree
        tags=['unknown']
        lastTime=time()
        while(running):
            for dev in dev1,dev2:
                if dev.getsFrom:
                    msg=dev.recieve()
                    if len(msg)>0:
                        #time
                        thisTime=time()
                        deltaTime=thisTime-lastTime
                        lastTime=thisTime
                        #log
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
                        #parse
                        parsed = dev.parse(msg)
                        debug(parsed)
                        # scroll if cursor at bottom
                        if(main_curr==len(convo_log)-2):
                            main_curr+=1
                            log_offset+=1
                        # pass to other device
                        dev.send(msg)
                        if(curr_mode=="parseTree"):
                            move_tree_curr = (tree_curr == len(parseTree)-1)
                            old_len = len(parseTree)
                            freshenParseTree()
                            new_len = len(parseTree)
                            if move_tree_curr:
                                tree_curr += new_len - old_len
                                if(tree_curr > lines-3):
                                    tree_offset += new_len - old_len
            count+=1
            sleep(convo_rate)
    except Exception:
        print(traceback.format_exc(),end="\n\r")
        running=False
convoThread = threading.Thread(target=convoLoop)
convoThread.start()

def freshenParseTree():
    global dev1,dev2,parseTree,parseTreeLock
    parseTreeLock=True
    d1tree=dev1.getTable()
    d2tree=dev2.getTable()
    newParseTree = []
    for row in d1tree:
        newParseTree+=[[dev1.name]+row]
    for row in d2tree:
        newParseTree+=[[dev2.name]+row]
    parseTree=newParseTree
    parseTreeLock=False

######################
## Human Input loop ##
######################
try:
    gg=False
    # hide cursor
    print("\033[?25l",end="")
    while(running):
        inp=getch()
        debug(inp)
        if(inp=="q"):
            running=False
        elif(inp=="m"):
            curr_info="main"
            curr_mode="main"
        elif(inp=="p"):
            curr_mode="parseTree"
            freshenParseTree()
        ### Parse Tree Control ###
        elif curr_mode=="parseTree":
            ### motion controls ###
            ## gg latch ##
            if(inp=="g"):
                if(gg):
                    tree_curr=0
                    tree_offset=0
                else:
                    gg=True
            else:
                gg=False
            ## other motion ##
            if(inp=="j"):
                tree_curr+=1
                if(tree_curr==len(parseTree)):
                    tree_curr=len(parseTree)-1
                elif(tree_curr>tree_offset+lines-2):
                    tree_offset+=1
            elif(inp=="k"):
                tree_curr-=1
                if(tree_curr==-1):
                    tree_curr=0
                elif(tree_curr<tree_offset):
                    tree_offset-=1
            elif(inp=="h"):
                tree_curr_h-=1
                if(tree_curr_h<0):
                    tree_curr_h=0
            elif(inp=="l"):
                tree_curr_h+=1
            elif(inp=="G"):
                tree_curr=len(parseTree)-1
                tree_offset=max(len(parseTree)-lines+2,0)
            elif(inp==""):
                tree_curr+=int(lines/2)
                tree_offset+=int(lines/2)
                if(tree_curr>=len(parseTree)):
                    tree_curr=len(parseTree)-1
                if(tree_offset>=len(parseTree)-lines+1):
                    tree_offset=len(parseTree)-lines+1
            elif(inp==""):
                tree_curr-=int(lines/2)
                tree_offset-=int(lines/2)
                if(tree_curr<0):
                    tree_curr=0
                if(tree_offset<0):
                    tree_offset=0
        ### Main Control ###
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
            ## other motion ##
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
            elif(inp==""):
                main_curr+=int(lines/2)
                log_offset+=int(lines/2)
                if(main_curr>=len(convo_log)):
                    main_curr=len(convo_log)-1
                if(log_offset>=len(convo_log)-lines+1):
                    log_offset=len(convo_log)-lines+1
            elif(inp==""):
                main_curr-=int(lines/2)
                log_offset-=int(lines/2)
                if(main_curr<0):
                    main_curr=0
                if(log_offset<0):
                    log_offset=0
            ### other main stuff ###
            elif(inp=="c"):
                curr_info="config"
                curr_mode="config"
            elif(inp=="t"):
                curr_mode="tags"
                curr_info="tags"
        ## Config input ##
        elif curr_mode=="config":
            if(inp=="c"):
                prev_info=curr_info
                curr_info="connect"
                inp=getch()
                if(inp=="1" or inp=="a"):
                    com1=serial.Serial( *conf["dev1"][1], timeout=0)
                if(inp=="2" or inp=="a"):
                    com2=serial.Serial( *conf["dev2"][1], timeout=0)
                dev1.getsFrom,dev1.sendsTo = com1, com2
                dev2.getsFrom,dev2.sendsTo = com2, com1
                curr_info=prev_info
            elif(inp=="n"):
                pass
            elif(inp=="p"):
                pass
            elif(inp=="b"):
                pass
            elif(inp=="d"):
                prev_info=curr_info
                curr_info="connect"
                inp=getch()
                if(inp=="1" or inp=="a"):
                    dev1=None
                if(inp=="2" or inp=="a"):
                    dev2=None
                dev1.getsFrom,dev1.sendsTo = com1, com2
                dev2.getsFrom,dev2.sendsTo = com2, com1
                curr_info=prev_info

        ## Tags input ##
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
    print(traceback.format_exc(),end="\n\r")
    running=False

#default white text...
print("\033[1;37m",end="")
# show cursor
print("\033[?25h",end="")
