import socket, threading, sys, os, glob
from functions import *
from consts import *

LOCALHOST = "127.0.0.1"
SERVER_PORT = int(sys.argv[1])
ADMIN_PW = sys.argv[2]

currUsers = []
currForumThreads = []
currThreads = []
uploadedFiles = []

shutdown = False

# Split up threads for each client
class ThreadController(threading.Thread):
  # Initialise thread and assign socket to thread
  def __init__(self, addr, sock):
    global currThreads
    threading.Thread.__init__(self)
    self.threadSocket = sock
    currThreads.append(self)
    print(CLIENT_CONNECTED)

  # Run thread unless global shutdown called
  def run(self):
    global shutdown
    while not shutdown:
      currUsername = auth(self)
      forum(self, currUsername, WELCOME)
      break
    return

# Handles login and signup
def auth(thread, retryMsg=""):
  sendData(thread, retryMsg + "\n" + ENTER_USERNAME)

  inpUsername = receiveData(thread)
  users = loadUsers()

  if authAlreadyLoggedIn(thread, inpUsername):
    return auth(thread, f"{inpUsername} has already logged in")

  # No username -> make account
  if inpUsername not in users:
    print("New user")
    sendData(thread, f"Enter new password for {inpUsername}: ")
    inpPassword = receiveData(thread)

    if authAlreadyLoggedIn(thread, inpUsername):
      return auth(thread, f"{inpUsername} has already logged in")
      
    createUser(inpUsername, inpPassword)
    return authSuccessful(inpUsername)

  if authAlreadyLoggedIn(thread, inpUsername):
    return auth(thread, f"{inpUsername} has already logged in")

  sendData(thread, ENTER_PASSWORD)
  inpPassword = receiveData(thread)

  # Bad password -> retry auth
  if users[inpUsername] != inpPassword:
    return auth(thread, INVALID_PASSWORD)

  if authAlreadyLoggedIn(thread, inpUsername):
    return auth(thread, f"{inpUsername} has already logged in")

  return authSuccessful(inpUsername)

def authAlreadyLoggedIn(thread, username):
  if username in currUsers:
    print(f"{username} has already logged in")
    return True
  return False

def authSuccessful(username):
  currUsers.append(username)
  print(f"{username} successful login")
  return username

# Main controller for validating commands and distributing commands to functions
def commandController(thread, username, cmdCode, args):
  splitArgs = args.split(" ")
  lenArgs = len(splitArgs)

  if cmdCode == "CRT":
    print(f"{username} issued CRT command")
    if lenArgs != 2:
      return forum(thread, username, INVALID_SYNTAX + cmdCode)
    return commandCreateThread(thread, username, splitArgs[1])
  elif cmdCode == "MSG":
    print(f"{username} issued MSG command")
    if lenArgs < 3:
      return forum(thread, username, INVALID_SYNTAX + cmdCode)
    return commandCreateMessage(thread, username, splitArgs[1], " ".join(splitArgs[2:]))
  elif cmdCode == "DLT":
    print(f"{username} issued DLT command")
    if lenArgs != 3:
      return forum(thread, username, INVALID_SYNTAX + cmdCode)
    return commandDeleteMessage(thread, username, splitArgs[1], splitArgs[2])
  elif cmdCode == "EDT":
    print(f"{username} issued EDT command")
    if lenArgs < 4:
      return forum(thread, username, INVALID_SYNTAX + cmdCode)
    return commandEditMessage(thread, username, splitArgs[1], splitArgs[2], " ".join(splitArgs[3:]))
  elif cmdCode == "LST":
    print(f"{username} issued LST command")
    if lenArgs != 1:
      return forum(thread, username, INVALID_SYNTAX + cmdCode)
    return commandListThreads(thread, username)
  elif cmdCode == "RDT":
    print(f"{username} issued RDT command")
    if lenArgs != 2:
      return forum(thread, username, INVALID_SYNTAX + cmdCode)
    return commandReadThread(thread, username, splitArgs[1])
  elif cmdCode == "UPD":
    print(f"{username} issued UPD command")
    if lenArgs != 3:
      return forum(thread, username, INVALID_SYNTAX + cmdCode)
    return commandUploadFile(thread, username, splitArgs[1], splitArgs[2])
  elif cmdCode == "DWN":
    print(f"{username} issued DWN command")
    if lenArgs != 3:
      return forum(thread, username, INVALID_SYNTAX + cmdCode)
    return commandDownloadFile(thread, username, splitArgs[1], splitArgs[2])
  elif cmdCode == "RMV":
    print(f"{username} issued RMV command")
    if lenArgs != 2:
      return forum(thread, username, INVALID_SYNTAX + cmdCode)
    return commandRemoveThread(thread, username, splitArgs[1])
  elif cmdCode == "XIT":
    print(f"{username} issued XIT command")
    if lenArgs != 1:
      return forum(thread, username, INVALID_SYNTAX + cmdCode)
    return commandExit(thread, username)
  elif cmdCode == "SHT":
    print(f"{username} issued SHT command")
    if lenArgs != 2:
      return forum(thread, username, INVALID_SYNTAX + cmdCode)
    return commandShutdown(thread, username, splitArgs[1])
  else: 
    return forum(thread, username, INVALID_COMMAND)
  
# CRT command
def commandCreateThread(thread, username, forumThreadName):
  res = createThread(forumThreadName, username, currForumThreads)
  if res == ERROR_THREAD_ALREADY_EXISTS:
    print(f"Thread {forumThreadName} exists")
    return forum(thread, username, f"Thread {forumThreadName} exists")
  
  currForumThreads.append(forumThreadName)
  print(f"Thread {forumThreadName} created")
  return forum(thread, username, f"Thread {forumThreadName} created")

# MSG command
def commandCreateMessage(thread, username, forumThreadName, message):
  res = createMessage(forumThreadName, message, username, currForumThreads)
  if res == ERROR_THREAD_NOT_EXIST:
    print(f"Thread {forumThreadName} does not exist")
    return forum(thread, username, f"Thread {forumThreadName} does not exist")

  print(f"Message posted to {forumThreadName} thread")
  return forum(thread, username, f"Message posted to {forumThreadName} thread")

# DLT command
def commandDeleteMessage(thread, username, forumThreadName, messageNum):
  res = deleteMessage(forumThreadName, username, messageNum, currForumThreads)
  if res == ERROR_THREAD_NOT_EXIST:
    print(f"Thread {forumThreadName} does not exist")
    return forum(thread, username, f"Thread {forumThreadName} does not exist")
  elif res == ERROR_MESSAGE_MODIFY_NO_PERMS:
    print("User does not have permission to delete message")
    return forum(thread, username, "This message belongs to another user and you do not have permission to edit/delete it")
  elif res == ERROR_MESSAGE_NUMBER_INVALID:
    print("Message number is not a number")
    return forum(thread, username, INVALID_SYNTAX + "DLT")
  elif res == ERROR_MESSAGE_NOT_FOUND:
    print(f"Message {messageNum} does not exist")
    return forum(thread, username, f"Message {messageNum} does not exist")
  
  print("Message has been deleted")
  return forum(thread, username, "The message has been deleted")

# EDT command
def commandEditMessage(thread, username, forumThreadName, messageNum, message):
  res = editMessage(forumThreadName, username, messageNum, message, currForumThreads)
  if res == ERROR_THREAD_NOT_EXIST:
    print(f"Thread {forumThreadName} does not exist")
    return forum(thread, username, f"Thread {forumThreadName} does not exist")
  elif res == ERROR_MESSAGE_MODIFY_NO_PERMS:
    print("User does not have permission to delete message")
    return forum(thread, username, "This message belongs to another user and you do not have permission to edit/delete it")
  elif res == ERROR_MESSAGE_NUMBER_INVALID:
    print("Message number is not a number")
    return forum(thread, username, INVALID_SYNTAX + "DLT")
  elif res == ERROR_MESSAGE_NOT_FOUND:
    print(f"Message {messageNum} does not exist")
    return forum(thread, username, f"Message {messageNum} does not exist")

  print("Message has been edited")
  return forum(thread, username, "The message has been edited")

# LST command
def commandListThreads(thread, username):
  if len(currForumThreads) == 0:
    return forum(thread, username, "No threads to list")
  threadsStr = "The list of active threads: \n"
  for i in range(len(currForumThreads)):
    if i == len(currForumThreads) - 1:
      threadsStr += currForumThreads[i]
    else:
      threadsStr += currForumThreads[i] + "\n"

  return forum(thread, username, threadsStr)
  
# RDT command
def commandReadThread(thread, username, forumThreadName):
  res = readThread(forumThreadName, currForumThreads)
  if res == ERROR_THREAD_NOT_EXIST:
    print(f"Thread {forumThreadName} does not exist")
    return forum(thread, username, f"Thread {forumThreadName} does not exist")
  elif res == ERROR_THREAD_EMPTY:
    print(f"Thread {forumThreadName} read")
    return forum(thread, username, f"Thread {forumThreadName} is empty")
  
  print(f"Thread {forumThreadName} read")
  return forum(thread, username, res)

# UPD command
def commandUploadFile(thread, username, forumThreadName, filename):
  global uploadedFiles
  res = receiveFile(thread, username, forumThreadName, filename, currForumThreads)
  if res == ERROR_THREAD_NOT_EXIST:
    print(f"Thread {forumThreadName} does not exist")
    return forum(thread, username, f"Thread {forumThreadName} does not exist")

  uploadedFiles.append(res)
  print(f"{username} uploaded file {filename} to {forumThreadName} thread")
  return forum(thread, username, f"{filename} uploaded to {forumThreadName} thread")

# DWN command
def commandDownloadFile(thread, username, forumThreadName, filename):
  res = sendFile(thread, forumThreadName, filename, currForumThreads)
  if res == ERROR_THREAD_NOT_EXIST:
    print(f"Thread {forumThreadName} does not exist")
    return forum(thread, username, f"Thread {forumThreadName} does not exist")
  if res == ERROR_DOWNLOAD_FILE_NOT_FOUND:
    print(f"{filename} does not exist in thread {forumThreadName}")
    return forum(thread, username, f"File does not exist in thread {forumThreadName}")
  if res == ERROR_INTERNAL_ERROR:
    print("An unknown internal error occured")
    return forum(thread, username, "An unknown internal error occured, please try again")

  print(f"{filename} downloaded from thread {forumThreadName}")
  return forum(thread, username, f"{filename} successfully downloaded")

# RMV command
def commandRemoveThread(thread, username, forumThreadName):
  res = removeThread(username, forumThreadName, currForumThreads)
  if res == ERROR_THREAD_NOT_EXIST:
    print(f"Thread {forumThreadName} does not exist")
    return forum(thread, username, f"Thread {forumThreadName} does not exist")
  elif res == ERROR_THREAD_DELETE_NO_PERMS:
    print(f"Thread {forumThreadName} cannot be removed")
    return forum(thread, username, f"Thread {forumThreadName} was created by another user and cannot be removed")

  currForumThreads.remove(forumThreadName)
  print(f"Thread {forumThreadName} removed")
  return forum(thread, username, f"Thread {forumThreadName} has been removed")

# XIT command
def commandExit(thread, username):
  currUsers.remove(username)
  sendData(thread, CLIENT_EXIT)
  thread.threadSocket.close()
  print(f"{username} exited")
  if len(currUsers) == 0:
    print("Waiting for clients")

# SHT command
def commandShutdown(thread, username, password):
  global shutdown
  global currThreads
  global uploadedFiles
  if password != ADMIN_PW:
    return forum(thread, username, INVALID_ADMIN_PASSWORD)
  # TODO: delete all files etc
  # Delete relevant files
  try:
    os.remove('credentials.txt')
    for forumThread in currForumThreads:
      if os.path.exists(forumThread):
        os.remove(forumThread)
    for file in uploadedFiles:
      if os.path.exists(file):
        os.remove(file)
  except:
    pass
  # Kill threads
  for thisThread in currThreads:
    thisThread.threadSocket.close()
    currThreads.remove(thisThread)
  print(SERVER_SHUTDOWN)
  shutdown = True
  # Force quit all and threads
  server.close()
  os._exit(1)

# Forum instance - will return to itself at all cases unless shutdown or exited
def forum(thread, username, preMsg=""):
  sendData(thread, preMsg + "\n" + ENTER_COMMANDS)
  inpArgs = receiveData(thread)
  try:
    cmdCode = inpArgs.split(" ", 1)[0]
    return commandController(thread, username, cmdCode, inpArgs)
  except Exception as err:
    # Unhandled error in command logic
    return forum(thread, username, "Invalid command - something unexpected happened\n" + err)

# Set up server and TCP sockets for listening
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, SERVER_PORT))
server.listen(1)

print("Waiting for clients")

# Accept sockets and distribute to threads while alive
while True:
  try:
    getSocket, getAddr = server.accept()
    threadInstance = ThreadController(getAddr, getSocket)
    threadInstance.start()
  except:
    # Failed to accept new connections, i.e. server has closed
    # SHT case
    break

server.close()
