import serial
import threading
import time
import Lock

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
pwm = 0

def turnonmotors():
    Lock.acquire()
    #Turn on Motor 1
    ser.write("~PO041V\n")
    ser.write("~PO050V\n")

    #Turn on Motor 2
    ser.write("~PO120V\n")
    ser.write("~PO131V\n")

    ramp = "rampup"

    ser.flush()
    Lock.release()

def turnoffmotors():
    Lock.acquire()
    #Turn off Motor 1
    ser.write("~PO040V\n")
    ser.write("~PO050V\n")

    #Turn off Motor 2
    ser.write("~PO120V\n")
    ser.write("~PO130V\n")

    ser.flush()
    Lock.release()

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
        if ((start + ticks) - odo) < 20 and ramp != "rampdown":
            ramp = "rampdown"
        time.sleep(pollingtime)
    turnoffmotors()

def ramper():
    global pwm, ramp
    while portopen:
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

        Lock.acquire()
        ser.write("~PW09%s\n" % strpwm)
        ser.write("~PW10%s\n" % strpwm)
        ser.flush()
        Lock.release()

        if pwm == slowestspeed or pwm == 100:
            ramp = "donothing"

        if pwm < 5 or pwm > 100:
            raise Exception("Son of a mother took off on us, PWM = %d" % pwm)


def readInfo():
        global portopen
        data = ""
        while portopen:
            info = ser.readline()
            if info.startswith("odo"):
                odo = int(info[3:])
            elif info.startswith("ad"):
                prox = int(info[2:])
            elif info.startswith("Current heading:"):
                heading = float(info[len("Current heading:"):])
            else:
                portopen = False
                raise Exception("Ardruino threw some crazy garbage at us")

def connect(where="/dev/tty.usbserial"):
    ser = serial.Serial(where, 9600)
    threading.Thread(target=readInfo).start()

if __name__ == "__main__":
    usbname = input("What is the name of the usb port?")
    connect(usbname)
    print("""
Try the following commands:
    face [angle]
    move [ticks]
    
    """)

    while True:
        com = input("Command:")
        if com.startswith("face"):
            angle = int(com.split(" ")[1])
            faceangle(angle)
        elif com.startswith("move"):
            ticks = int(com.split(" ")[1])
            move(ticks)
        else:
            print("Sorry buddy, that's not a command: %s" % com)
