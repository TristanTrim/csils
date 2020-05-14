

import threading
import msvcrt
from time import sleep

running = True

def convoLoop():
    global running
    while(running):
        print("Hi",end="",flush=True)
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
