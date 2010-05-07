#!/usr/bin/python
################################################################################
# Default port: 21567                                                          #
# Default host: localhost                                                      #
#                                                                              #
# This daemon serves as the means of communicaton between client programs      #
# that want to control PatherBot and the physical COM port.                    #
#                                                                              #
# The protocol for communicating with this daemon is as follows:               #
# On connection to port daemon sends to client:                                #
#    "BUSY"  if daemon is already at maximum capcity of clients                #
#    "OK"    if daemon accepts the client                                      #
#                                                                              #
#                                                                              #
# Authors: Sandro Badame                                                       #
################################################################################
import getopt
import logging.handlers

import threading
import os
import socket
import sys
import diagnostic
import robo

#Open the com port
_serialport = ""
if os.name == 'posix': #Linux/Mac
    _serialport = "/dev/ttyUSB0" #@IndentOk
elif os.name == 'nt': #Windows
    _serialport = "COM3" #@IndentOk

#Internet address for clients attaching to this daemon
_hostname = "localhost" 
_port = 21567

#Open a webserver that will display the contents of the log file
_dport = 8000

def printHelp():
    print('''
usage: python pather-daemon.py COMMANDS
   --help      See this message
-p --port      The port to open for this daemon to bind to and for clients to attach to [default is %d]
-h --hostname  The host name for this daemon to bind to and for clients to attach to [default is %s]
-x             The daemon will not send commands through a serial port, but will instead print commands to standard out
-m --mute      The daemon will not make any sounds when a command is received [default is for sound to be made]
-s --serial    The serial device that this daemon will connect to [default is %s, Note: The default is OS dependent]
-d --dport     The daemon will start a webserver that will output the contents of the log file
''' % (_port, _hostname, _serialport))

#Handle logging
dir = __file__[:-9]
LOG_FILENAME = '%slog/pather-daemon.log' % dir
log = logging.getLogger('pather-daemon')
log.setLevel(logging.DEBUG)

#Log file
filehandler = logging.handlers.RotatingFileHandler(LOG_FILENAME)
filehandler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
log.addHandler(filehandler)

#Standard out log
consolehandler = logging.StreamHandler(sys.stdout)
consolehandler.setFormatter(logging.Formatter("%(message)s"))
log.addHandler(consolehandler)

#Output to serial port or is this a test run?
_USESERIAL = True

#Parse arguments passed to this script
try:
    opts, args = getopt.getopt(sys.argv[1:], "mxh:p:s:", ["help", "port=", "hostname=", "serial=", "mute"])
except:
    printHelp()
    sys.exit(2)

for opt, args in opts:
    if opt == "--help":
        printHelp()
        sys.exit()
    elif opt in ("-p", "--port"):
        _port = int(args)
    elif opt in ("-h", "--hostname"):
        _hostname = args
        log.info("-h option detected, hostname=%s" % _hostname)
    elif opt == "-x":
        _USESERIAL = False
        log.info("-x option detected, print output to STDOUT instead of the serial port")
    elif opt in ("-m", "--mute"):
        _USESOUND = False
        log.info("-m option detected, no sound will be played when commands are received.")
    elif opt in ("-s", "--serial"):
            _serialport = args
    log.info("-s option detected, using port=%s" % _serialport);

#connect to Arduino here
robo.connect(_serialport, _USESERIAL)

#Grab onto the socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server.bind((_hostname, _port))
except:
    log.error("Could not bind to port:%d" % _port)
    print("Could not bind to port:%d" % _port)
    sys.exit(2)

server.listen(0)
log.info("Listening to port %d for clients." % _port)

#Start the log diagnostic thread
diagnostic.startServer()

#get info from client
def read():
    data = ""
    while True:
        data += clientsocket.recv(4096)
        if not data:
            break
        #see if we can remove parts of data
        messagecount = data.count('\n')
        splitted = data.split("\n")
        for i in range(messagecount):
            message = splitted[i]
            if message.startswith("Move"):
                robo.move(int(message.split(",")[1]),int(message.split(",")[2]))
            elif message.startswith("Face"):
                robo.faceangle(int(message.split(",")[1]),int(message.split(",")[2]))
            elif message.startswith("Cancel"):
                robo.cancel(int(message.split(",")[1]))
            else:
                log.info("Bad command:" + message)
        data=data.rpartition("\n")[2]

    clientsocket.shutdown(socket.SHUT_RDWR)
    robo.stop()

#begin loop
while True:#waits for ppl to connect
    (clientsocket, address) = server.accept()
    log.info("Connection made from %s" % address)
    threading.Thread(target=read).start()
    robo.clientport = clientsocket
