#!/usr/bin/env python
# coding=utf-8

# note: if you are on linux, you might have to run
# with sudo
# If you don't want to run with sudo, you can try
# adding dialout to your user (requires a logout to
# take effect:
#    $ sudo usermod -a -G dialout $USER

import os
import sys
import time
import availablePorts
import serial

def parseMarkdown(text):
    BOLD_CODE = chr(2) # will be sent to arduino to toggle bold
    UNDERLINE_CODE = chr(3) # sent to arduino to toggle underline
    '''We are looking for __underline__ and **bold**
       text. Nothing fancy, and we are expecting that
       the markdown will be perfect (e.g., missing tags
       are not handled particularly gracefully)
       The basic idea: __ toggles underline and
       ** toggles bold. Either can be escaped with
       a leading backslash ('\').
    '''
    parsedText = ''
    escaped = False
    skipnext = False
    for idx,c in enumerate(text):
        if skipnext: 
            skipnext = False
            continue
        if escaped:
            parsedText += c
            escaped = False
        elif c == '\\': # look for escape character
            escaped = True
        elif c == '*':
            # lookahead one char
            if idx < len(text) - 1 and text[idx+1] == '*':
                parsedText+=BOLD_CODE
                skipnext = True
            else:
                parsedText+=c
        elif c == '_':
            # lookahead one char
            if idx < len(text) - 1 and text[idx+1] == '_':
                parsedText+=UNDERLINE_CODE
                skipnext = True
            else:
                parsedText+=c
        else:
            parsedText += c
    return parsedText

MAXLINE = 40
# if HARDCODED_PORT is '', then the user will get a choice
#HARDCODED_PORT = '/dev/tty.wchusbserial1410'
HARDCODED_PORT = ''

if len(sys.argv) == 1:
    print('Usage:\n\t%s "text to print" [microspacing] [serialPort]"'% sys.argv[0])
    quit()

allText = sys.argv[1]
spacing = int(sys.argv[2])
if len(sys.argv) > 3:
    portChoice = sys.argv[3]
else:
    portChoice = None
    portChoiceInt = 0
# choose port
if portChoice == None:
    if HARDCODED_PORT == '':
        ports = availablePorts.serial_ports()

        if len(ports) == 1:
            # just choose the first
            print("Choosing: " + ports[0])
            portChoice = ports[0]
        else:
            if portChoiceInt == 0:
                print("Please choose a port:")
                for idx,p in enumerate(ports):
                    print("\t"+str(idx+1)+") "+p)
                portChoiceInt = int(input())
            portChoice = ports[portChoiceInt-1]
    else: 
        portChoice = HARDCODED_PORT

# parse markdown, only looking for __text__ for underline
# and **text** for bold
remainingText = parseMarkdown(allText)

# set up serial port
ser = serial.Serial(portChoice, 115200, timeout=0.1)
# wait a bit
time.sleep(2)

# get the text length
textLen = len(remainingText) 

# first two bytes are the file length (max: 65K)
# sent in little-endian format
stringHeader = chr(0x00) + chr(textLen & 0xff) + chr(textLen >> 8) + chr(spacing)

try:
    # read MAXLINE characters at a time and send
    while len(remainingText) > 0:
        chars = remainingText[:MAXLINE]
        remainingText = remainingText[MAXLINE:]
        if chars == '':
            break
        ser.write(bytearray(stringHeader + chars,'utf-8'))
        stringHeader = ''  # not needed any more
        sys.stdout.write(chars)
        sys.stdout.flush()
        response = ""
        while True:
            response += ser.read(10).decode('utf-8')
            #print("resp:"+response)
            if len(response) > 0 and response[-1] == '\n':
                print("response: "+response)
                break
            time.sleep(0.1)
except KeyboardInterrupt:
    pass
ser.close()
