

import threading
from time import sleep
import subprocess
import msvcrt # needs unix portablility

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

#menu vars
info={
        "help":lambda:"q-quit c-config ?-help",
        "config":lambda:"n-name c-comm b-baud"
        }
curr_info="help"

def updateDisplay():
    global curr_info
    #clear
    print("\033[F\033[K"*lines,end="")
    print(info[curr_info]())
    for ii in range(lines-1):
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
    elif(inp==b"c"):
        curr_info="config"
    elif(inp==b"?"):
        curr_info="help"



