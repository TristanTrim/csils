

import threading
from time import sleep
import subprocess
import msvcrt # needs unix portablility
import json

# terminal line control hack
_=subprocess.call("",shell=True)

# data vars
count = 0

# config vars
lines = 13
print("\n"*lines)
display_rate = .2
convo_rate = .01
running = True
default_conf_file = "conf"

#menu vars
info={
        "help":lambda:"q-quit c-config",
        "config":lambda:"n-name c-comm b-baud m-main",
        "conf":lambda:str(conf),
        }
curr_info="help"
curr_mode="main"

#load default conf
conf=json.load(open("conf",'r'))

def updateDisplay():
    global curr_info, curr_mode
    #clear
    print("\033[F\033[K"*lines,end="")
    print(info[curr_info]())
    if(curr_mode=="main"):
        for ii in range(lines-1):
            print("%8d"%count,"foo")
    elif(curr_mode=="config"):
        print(conf["dev1"])
        print(conf["dev2"])
        for ii in range(lines-1-2):
            print("%8d"%count,"foo")

def displayLoop():
    global running
    while running:
        updateDisplay()
        sleep(display_rate)
displayThread = threading.Thread(target=displayLoop)
displayThread.start()

###########
## Convo ##
###########
def convoLoop():
    global running
    global count
    while(running):
        count+=1
        sleep(convo_rate)
convoThread = threading.Thread(target=convoLoop)
convoThread.start()

#UI loop
while(running):
    inp=msvcrt.getch()
    if(inp==b"q"):
        running=False
    elif curr_mode=="main":
        if(inp==b"c"):
            curr_info="config"
            curr_mode="config"
    elif curr_mode=="config":
        if(inp==b"m"):
            curr_info="help"
            curr_mode="main"



