import time
import random

odocount = 0
heading = 150.34

def write(msg):
    print("dummyserial.py " + msg)

def flush():
    pass

def readline():
    global odocount, heading
    time.sleep(random.random()*5) #The daemon will go crazy if this doesn't block for a bit
    if random.random() > 0.5:
        odocount += random.randint(2, 8)
        return "odo%d" % odocount
    else:
        heading += random.randint(1,999)/100.0
        if heading >= 360:
            heading -= 360
        return "Current heading: %.2f degrees" % heading
    return "Ufa"
