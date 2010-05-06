import serial
import threading
import time

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

#De lock
lock = threading.Lock()

def turnonmotors():
    global ramp
    lock.acquire()
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
    lock.release()


def turnoffmotors():
    lock.acquire()
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

    lock.release()

def stop():
    turnoffmotors()

def turn_clockwise():
    lock.acquire()

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

    lock.release()


def turn_counterclockwise():
    lock.acquire()
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

    lock.release()

def faceangle(angle):
    turn_clockwise()
    while abs(angle-heading) > headingaccuracy:
        print("Aiming for %s, currently facing %s" % (angle, heading))
        time.sleep(0.5)
    turnoffmotors()

def move(ticks):
    global ramp
    start = odo
    end = odo + ticks
    turnonmotors()
    #print("Starting to move from %d to %d" % (start,end))
    while odo < end:
        print("odo at : " + str(odo) )
        if (end - odo) < 20 and ramp != rampdown:
            ramp = rampdown
        time.sleep(pollingtime)
    #print("Done with loop")
    turnoffmotors()

def ramper():
    global pwm, ramp
    while portopen:
        lock.acquire()
        if ramp == rampup:
            pwm += 3
        elif ramp == rampdown:
            pwm -= 3
        elif ramp == donothing:
            lock.release()
            continue
        else:
            lock.release()
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
        lock.release()
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

def connect(where="/dev/tty.usbserial"):
    global ser
    ser = serial.Serial(where, 9600)
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
            faceangle(angle)
        elif com.startswith("move"):
            ticks = int(com.split(" ")[1])
            move(ticks)
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
