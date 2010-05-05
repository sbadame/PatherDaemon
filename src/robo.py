import serial
import threading
import time

#Needs to be calibrated
pollingtime = 0.5
headingaccuracy = 5
slowestspeed = 5

#This will hold the connection to the arduino
ser = None
odo = 0
prox = 0
heading = 0
portopen = True

#Current PWM amount
ramp = "donothing"
pwm = 3

#De lock
lock = threading.Lock()

def turnonmotors():
    lock.acquire()
    print("on Aqui")
    #Turn on Motor 1
    ser.write("~PO041V")
    ser.write("~PO050V")

    #Turn on Motor 2
    ser.write("~PO120V")
    ser.write("~PO131V")

    ramp = "rampup"

    ser.flush()
    print("on release")
    lock.release()

def turnoffmotors():
    lock.acquire()
    print("off aq")
    #Turn off Motor 1
    ser.write("~PO040V\n")
    ser.write("~PO050V\n")

    #Turn off Motor 2
    ser.write("~PO120V\n")
    ser.write("~PO130V\n")

    ser.flush()
    print("off rel")
    lock.release()

def turn_clockwise():
    ramp = "donothing"

    #Reverse Motor 1
    ser.write("~PO040V\n")
    ser.write("~PO051V\n")

    #Forwards Motor 2
    ser.write("~PO120V\n")
    ser.write("~PO131V\n")

    ser.flush()


def turn_counterclockwise():
    ramp = "donothing"

    #Forwards Motor 1
    ser.write("~PO041V\n")
    ser.write("~PO050V\n")

    #Reverse Motor 2
    ser.write("~PO121V\n")
    ser.write("~PO130V\n")

    ser.flush()

def faceangle(angle):
    while abs(angle-heading) > headingaccuracy:
        turn_clockwise()

def move(ticks):
    global ramp
    start = odo
    turnonmotors()
    while odo < start + ticks:
        #print("odo: %d" % odo)
        if ((start + ticks) - odo) < 20 and ramp != "rampdown":
            ramp = "rampdown"
        time.sleep(pollingtime)
    turnoffmotors()

def ramper():
    global pwm, ramp
    while portopen:
        time.sleep(pollingtime)
        if ramp == "rampup":
            pwm += 3
        elif ramp == "rampdown":
            pwm -= 3
        elif ramp == "donothing":
            continue
        else:
            raise Exception("bad value for ramp: %s" % ramp)

        pwm = pwm if pwm > slowestspeed else slowestspeed
        pwm = pwm if pwm < 100 else 100

        strpwm = str(pwm) if pwm >= 10 else "0"+str(pwm)

        lock.acquire()
        print("ramp Aqui")
        ser.write("~PM09%s" % strpwm)
        ser.write("~PM10%s" % strpwm)
        ser.flush()
        print("ramp Rel")
        lock.release()

        if pwm == slowestspeed or pwm == 100:
            ramp = "donothing"

        if pwm < 5 or pwm > 100:
            raise Exception("Son of a mother took off on us, PWM = %d" % pwm)


def readInfo():
        global portopen,odo,heading,prox
        data = ""
        while portopen:
            print("reading info")
            info = ser.readline()
            if info.startswith("odo"):
                print("Got odo command: %s" % info)
                odo = int(info[3:])
            elif info.startswith("ad"):
                prox = int(info[2:])
            elif info.startswith("Current heading:"):
                heading = float(info.split(" ")[2])
            elif info == "\n" or info.startswith("Ufa"):
                pass
            elif info.startswith("echo"):
                print("Got message: %s" % info.split(" ", 1)[1])
            else:
                portopen = False
                raise Exception("Ardruino threw some crazy garbage at us: \"%s\"" % info)

def connect(where="/dev/tty.usbserial"):
    global ser
    ser = serial.Serial(where, 9600)
    threading.Thread(target=readInfo).start()
    threading.Thread(target=ramper).start()

if __name__ == "__main__":
    connect("/dev/ttyUSB0")
    while True:
        com = raw_input("Command:")
        print(com)
        if com.startswith("face"):
            angle = int(com.split(" ")[1])
            faceangle(angle)
        elif com.startswith("move"):
            ticks = int(com.split(" ")[1])
            move(ticks)
        else:
            print("Sorry buddy, that's not a command: %s" % com)
