

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
running = True

#menu vars
info={
        "help":lambda:"q-quit c-config ?-help",
        "config":lambda:"n-name c-comm b-baud"
        }
curr_info="help"

def clear():
    print("\033[F\033[K"*lines,end="")
def updateDisplay():
    global curr_info
    clear()
    print(info[curr_info]())
    for ii in range(lines-1):
        print("%8d"%count,"foo")

def convoLoop():
    global running
    global count
    while(running):
        count+=1
        updateDisplay()
        sleep(.1)
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



