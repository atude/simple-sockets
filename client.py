import socket, sys
from functions import *

SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, SERVER_PORT))

sentData = ""

while True:
  recvData = client.recv(1024)
  data = recvData.decode()
  msg = data.strip()

  if msg == EXIT_CONNECTION:
    print(msg)
    break
  elif msg == UPD_CONFIRM_UPLOAD:
    try:
      splitRecv = sentData.split(" ")
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
    while recvsize < filesize:
      recvFile = client.recv(2048)
      recvsize += len(recvFile)
      # Append to buffer
      if buffer == None:
        buffer = recvFile
      else:
        buffer += recvFile
    f = open(filename, "wb")
    f.write(buffer)
    f.close()
    client.sendall(formatText(DWN_FINISHED_DOWNLOAD))
  else:
    print(msg)
    sentData = input()
    client.sendall(formatText(sentData))

    

client.close()