import serial
import threading
import time
import dummyserial
import dummyclient

clientport = dummyclient

#Needs to be calibrated
pollingtime = 0.5
headingaccuracy = 5
slowestspeed = 30
hispeed = 90

#This will hold the connection to the arduino
ser = None
odo = 0
prox = 0
heading = 0
portopen = True

#Current PWM amount
donothing = 0
rampup = 1
rampdown = 2
ramp = donothing
pwm = slowestspeed

#De seriallock
seriallock = threading.Lock()
commandlock = threading.Lock()

#dictionary of commands
commanddict = {}

def turnonmotors():
    global ramp
    seriallock.acquire()
    print("Turning on motors")
    ramp = rampup

    #Turn on Motor 1
    ser.write("~PO041V")
    ser.flush()
    ser.write("~PO050V")
    ser.flush()

    #Turn on Motor 2
    ser.write("~PO120V")
    ser.flush()
    ser.write("~PO131V")
    ser.flush()
    seriallock.release()

def turnoffmotors():
    seriallock.acquire()
    global ramp,pwm
    ramp = donothing
    pwm = slowestspeed
    #Turn off Motor 1
    ser.write("~PO040V")
    ser.flush()
    ser.write("~PO050V")
    ser.flush()

    #Turn off Motor 2
    ser.write("~PO120V")
    ser.flush()
    ser.write("~PO130V")
    ser.flush()

    seriallock.release()

def stop():
    turnoffmotors()

def turn_clockwise():
    seriallock.acquire()

    global ramp
    ramp = donothing
    #Reverse Motor 1
    ser.write("~PO040V")
    ser.flush()
    ser.write("~PO051V")
    ser.flush()

    #Forwards Motor 2
    ser.write("~PO120V")
    ser.flush()
    ser.write("~PO131V")
    ser.flush()

    #Turn on pulse width
    ser.write("~PM0950")
    ser.flush()

    seriallock.release()

def turn_counterclockwise():
    seriallock.acquire()
    global ramp
    ramp = donothing

    #Forwards Motor 1
    ser.write("~PO041V")
    ser.flush()
    ser.write("~PO050V")
    ser.flush()

    #Reverse Motor 2
    ser.write("~PO121V")
    ser.flush()
    ser.write("~PO130V")
    ser.flush()

    ser.write("~PM0950")
    ser.flush()

    seriallock.release()

def __faceangle(angle,ID=0):
    commandlock.acquire()
    global commanddict
    commanddict[ID]=True
    turn_clockwise()
    while abs(angle-heading) > headingaccuracy and commanddict[ID] == True:
        print("Aiming for %s, currently facing %s" % (angle, heading))
        time.sleep(0.5)
    turnoffmotors()
    clientport.sendall("Success," + str(ID))
    commandlock.release()

def faceangle(angle,ID=0):
    if commandlock.locked():
        clientport.sendall("Busy," + str(ID))
    else:
        threading.Thread(target=__faceangle,args=(angle,ID)).start()

def __move(ticks,ID=0):
    commandlock.acquire()
    global ramp, commanddict
    commanddict[ID]=True
    start = odo
    end = odo + ticks
    turnonmotors()
    #print("Starting to move from %d to %d" % (start,end))
    while odo < end and commanddict[ID] == True:
        print("odo at : " + str(odo) )
        if (end - odo) < 20 and ramp != rampdown:
            ramp = rampdown
        time.sleep(pollingtime)
    #print("Done with loop")
    turnoffmotors()
    clientport.sendall("Success," + str(ID))
    commandlock.release()

def move(ticks,ID=0):
    if commandlock.locked():
        clientport.sendall("Busy" + str(ID))
    else:
        threading.Thread(target=__move,args=(ticks,ID)).start()

def cancel(ID):
    global commanddict
    commanddict[ID] = False

def ramper():
    global pwm, ramp
    while portopen:
        seriallock.acquire()
        if ramp == rampup:
            pwm += 3
        elif ramp == rampdown:
            pwm -= 3
        elif ramp == donothing:
            seriallock.release()
            continue
        else:
            seriallock.release()
            raise Exception("bad value for ramp: \"%s\"" % ramp)

        time.sleep(pollingtime)
        if pwm <= slowestspeed:
            pwm = slowestspeed
        if pwm >= hispeed:
            pwm = hispeed

        rmpmsg09 = "~PM09" + str(pwm)
        #rmpmsg10 = "~PM10" + str(pwm)
        #print("Sending: " + rmpmsg09)
        #print("Sending: " + rmpmsg10)
        #ser.write(rmpmsg10)
        ser.write(rmpmsg09)
        ser.flush()

        if pwm <= slowestspeed or pwm >= hispeed:
            ramp = donothing

        if pwm < slowestspeed or pwm > hispeed:
            raise Exception("Son of a mother took off on us, I'll throw an Exception at him! PWM = %d" % pwm)
        seriallock.release()
        time.sleep(pollingtime)

def readInfo():
        global portopen,odo,heading,prox
        data = ""
        while portopen:
            info = ser.readline()
            #print("read in: " + info)
            if info.startswith("odo"):
                odo = int(info[3:])
            elif info.startswith("ad"):
                prox = int(info[2:])
            elif info.startswith("Current"):
                heading = float(info.split(" ")[2])
            elif info.startswith("echo"):
                print(info)
            elif info == "\n" or info.startswith("Ufa"):
                pass
            else:
                print("Ardruino threw some crazy garbage at us: \"%s\"" % info)

def connect(where="/dev/ttyUSB0", useserial=True):
    global ser
    if useserial == True:
        ser = serial.Serial(where, 9600)
    else:
        ser = dummyserial
    threading.Thread(target=readInfo).start()
    threading.Thread(target=ramper).start()

if __name__ == "__main__":
    connect("/dev/ttyUSB0")
    while True:
        com = raw_input("Command:")
        if com.isspace():
            continue
        elif com.startswith("face"):
            angle = int(com.split(" ")[1])
            __faceangle(angle)
        elif com.startswith("move"):
            ticks = int(com.split(" ")[1])
            __move(ticks)
        elif com.startswith("on"):
            turnonmotors()
        elif com.startswith("off"):
            turnoffmotors()
        elif com.startswith("cw"):
            turn_clockwise()
        elif com.startswith("ccw"):
            turn_counterclockwise()
	elif com.startswith("stop"):
	    stop()
	elif com.startswith("exit"):
	    stop()
	    exit()
        else:
            print("Sorry buddy, that's not a command: %s" % com)
