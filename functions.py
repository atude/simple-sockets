from time import sleep
import os
from consts import *

#
#
# Client/server helpers
#
#

# Format text for sending
def formatText(txt):
  return bytes(txt, 'UTF-8')

# Send data from server 
def sendData(thread, msg):
  thread.threadSocket.send(formatText(msg))
  sleep(1)
  return 

# Receive data (i.e. commands) from client
def receiveData(thread):
  data = ''
  while True: 
    data = thread.threadSocket.recv(2048)
    data = data.decode()
    data = data.strip()
    if data:
      break
  return data

# Receive file from client
# First get file size, then file
def receiveFile(thread, username, threadName, filename):
  if not os.path.exists(threadName):
    return ERROR_THREAD_NOT_EXIST

  buffer = None
  while True: 
    # Confirm upload to client
    sendData(thread, UPD_CONFIRM_UPLOAD)
    filesize = thread.threadSocket.recv(2048)
    filesize = int(filesize.decode())
    sendData(thread, UPD_START_UPLOAD)
    recvsize = 0
    print(f"Receiving file of size {str(filesize)} bytes")
    while recvsize < filesize:
      data = thread.threadSocket.recv(2048)
      recvsize += len(data)
      # Append to buffer
      if buffer == None:
        buffer = data
      else:
        buffer += data
    if buffer:
      break
  # Write to file
  f = open(f"{threadName}-{filename}", "wb")
  f.write(buffer)
  f.close()
  # Append to thread
  f = open(threadName, "a")
  f.write(f"{username} uploaded {filename}\n")
  f.close()
  return SUCCESS

#
#
# Auth and preparation
#
#

def loadUsers():
  f = open("credentials.txt", "r")
  lines = f.readlines()
  users = {}
  for line in lines:
    username, password = line.rstrip().split(' ')
    users[username] = password
  f.close()
  return users

def createUser(username, password):
  f = open("credentials.txt", "a+")

  # Check if there is need for new line
  f.seek(0)
  checkData = f.read(100)
  if len(checkData) > 0:
    f.write("\n")

  f.write(f"{username} {password}")
  f.close()
  return

#
#
# Forum thread command helpers
#
#

# CRT helper
def createThread(threadName, username):
  if os.path.exists(threadName):
    return ERROR_THREAD_ALREADY_EXISTS
  f = open(threadName, "a")
  f.write(f"{username}\n")
  f.close()
  return SUCCESS

# MSG helper
def createMessage(threadName, message, username):
  if not os.path.exists(threadName):
    return ERROR_THREAD_NOT_EXIST
  f = open(threadName, "r")
  lines = f.readlines()
  lastLine = 0

  # Get latest first number in lines
  for line in lines:
    num = line.split(" ")[0]
    try:
      num = int(num)
      lastLine = num
    except:
      pass
  
  lastLine += 1
  f.close()

  f = open(threadName, "a")
  f.write(f"{lastLine} {username}: {message.strip()}\n")
  f.close()
  return SUCCESS

# RDT helper
def readThread(threadName, currThreads):
  if not os.path.exists(threadName):
    return ERROR_THREAD_NOT_EXIST
  if threadName not in currThreads:
    return ERROR_THREAD_NOT_EXIST
  f = open(threadName, "r")

  # Remove first line
  lines = f.readlines()[1:]
  f.close()

  if len(lines) == 0:
    return ERROR_THREAD_EMPTY

  # Remove newline
  lines[-1] = lines[-1].rstrip()
  return "".join(lines)

# RMV helper
def removeThread(username, threadName, currThreads):
  if not os.path.exists(threadName):
    return ERROR_THREAD_NOT_EXIST
  if threadName not in currThreads:
    return ERROR_THREAD_NOT_EXIST
  f = open(threadName, "r")
  threadCreator = f.readlines()[0].strip()
  if threadCreator != username:
    return ERROR_THREAD_DELETE_NO_PERMS
  
  f.close()
  os.remove(threadName)
  return SUCCESS

# DLT helper
def deleteMessage(threadName, username, messageNum):
  if not os.path.exists(threadName):
    return ERROR_THREAD_NOT_EXIST

  # Parse inp message number
  try:
    messageNum = int(messageNum)
  except:
    return ERROR_MESSAGE_NUMBER_INVALID

  f = open(threadName, "r")
  lines = f.readlines()
  f.close()
  
  # Iterate through messages 
  foundLine = False
  finalLines = []
  currLineNum = 0

  for line in lines:
    sections = line.split(" ")

    # Not a message
    if len(sections) < 3:
      finalLines.append(line)
      continue

    num = sections[0]
    msgCreator = sections[1]
    
    # Add all lines except to be deleted line
    try:
      num = int(num)
      if num == messageNum:
        # User is creator of msg
        if msgCreator == f"{username}:":
          # Skip adding to be deleted line
          foundLine = True
          currLineNum = num
        else:
          return ERROR_MESSAGE_MODIFY_NO_PERMS
      else:
        # Add to line number
        updatedLine = line
        if foundLine:
          updatedLine = str(currLineNum) + " " + " ".join(sections[1:])
          currLineNum += 1
        finalLines.append(updatedLine)

    except:
      # Not a message
      finalLines.append(line)

  if not foundLine:
    return ERROR_MESSAGE_NOT_FOUND
    
  # Write to file if passes correctly
  f = open(threadName, "w")
  f.writelines(finalLines)
  f.close()
  return

def editMessage(threadName, username, messageNum, message):
  if not os.path.exists(threadName):
    return ERROR_THREAD_NOT_EXIST

  # Parse inp message number
  try:
    messageNum = int(messageNum)
  except:
    return ERROR_MESSAGE_NUMBER_INVALID

  f = open(threadName, "r")
  lines = f.readlines()
  f.close()
  
  # Iterate through messages 
  finalLines = []
  foundLine = False

  for line in lines:
    sections = line.split(" ")

    # Not a message
    if len(sections) < 3:
      finalLines.append(line)
      continue

    num = sections[0]
    msgCreator = sections[1]
    
    # Add all lines and modify chosen one
    try:
      num = int(num)
      if num == messageNum:
        # User is creator of msg
        if msgCreator == f"{username}:":
          # Edit current line
          foundLine = True
          editedLine = f"{str(num)} {msgCreator} {message.strip()}\n"
          finalLines.append(editedLine)
        else:
          return ERROR_MESSAGE_MODIFY_NO_PERMS
      else:
        # Add to line number
        finalLines.append(line)

    except:
      # Not a message
      finalLines.append(line)

  if not foundLine:
    return ERROR_MESSAGE_NOT_FOUND
    
  # Write to file if passes correctly
  f = open(threadName, "w")
  f.writelines(finalLines)
  f.close()
  return

  

  
  






