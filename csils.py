

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

def clear():
    print("\033[F\033[K"*lines,end="")
def updateDisplay():
    clear()
    for ii in range(lines):
        print(count,"foo")

def convoLoop():
    global running
    global count
    while(running):
        count+=1
        updateDisplay()
        sleep(2)
convoThread = threading.Thread(target=convoLoop)
convoThread.start()

#UI loop
while(running):
    inp=msvcrt.getch()
    if(inp==b"q"):
        running=False
    else:
        print(inp)
