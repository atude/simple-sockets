import socket, sys, select
from functions import *

SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, SERVER_PORT))

sockets = [sys.stdin, client]

sentData = ""
shutdown = False

while True:
  recvData = client.recv(1024)

  # Shutdown
  if len(recvData) == 0:
    if not shutdown:
      print(CLIENT_SHUTDOWN)
    break
  data = recvData.decode()
  msg = data.strip()

  if msg == CLIENT_EXIT:
    # User exit case -> quit safely
    print(msg)
    break
  elif msg == UPD_CONFIRM_UPLOAD:
    # Attempt upload
    try:
      # Load file data as binary
      splitRecv = sentData.strip().split(" ")
      filename = splitRecv[2]
      f = open(filename, "rb")
      l = f.read()
      f.close()

      # Send and request acknowledgement of file size 
      client.sendall(str(len(l)).encode())
      recvFilesizeAck = client.recv(1024)
      filesizeAck = recvFilesizeAck.decode()
      
      if filesizeAck == UPD_START_UPLOAD:
        client.sendall(l)
      else:
        raise Exception("Did not receive confirmation from server")
    except Exception as e:
      print("Something unexpected happened\n" + e)
  elif msg == DWN_CONFIRM_DOWNLOAD:
    # Sent acknowledgement of download and wait for filesize
    filename = sentData.strip().split(" ")[2]
    client.sendall(formatText(DWN_READY_DOWNLOAD))
    recvFilesize = client.recv(1024)
    filesize = int(recvFilesize.decode())
    client.sendall(formatText(DWN_START_DOWNLOAD))

    recvsize = 0
    buffer = None

    # Start downloading
    while recvsize < filesize:
      recvFile = client.recv(2048)
      recvsize += len(recvFile)
      # Append to buffer
      if buffer == None:
        buffer = recvFile
      else:
        buffer += recvFile
        
    # Write downloaded binary to file
    f = open(filename, "wb")
    f.write(buffer)
    f.close()

    # Send acknowledgement of successful download
    client.sendall(formatText(DWN_FINISHED_DOWNLOAD))
  else:
    # General case -> wait for user input or override via shutdown
    print(msg)
    inSockets, outputSockets, errSockets = select.select(sockets, [], [])
    for thisSocket in inSockets:
      if thisSocket == client:
        # Shutdown case
        recvData = client.recv(1024)
        # Verify shutdown, i.e. no received data
        if len(recvData) == 0:
          print(CLIENT_SHUTDOWN)
          shutdown = True
          break
      else: 
        # User input case
        sentData = sys.stdin.readline()
        client.sendall(formatText(sentData))

client.close()
