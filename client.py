import socket
from functions import *

SERVER = "127.0.0.1"
PORT = 8080

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER, PORT))

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
      f = open(filename, 'rb')
      l = f.read()

      # Send and request acknowledgement of file size 
      client.sendall(str(len(l)).encode())
      recvFilesizeAck = client.recv(1024)
      filesizeAck = recvFilesizeAck.decode()
      
      if filesizeAck == UPD_START_UPLOAD:
        client.sendall(l)
      else:
        raise Exception("Did not receive confirmation from client")
    except Exception as e:
      print("Something unexpected happened\n" + e)
  else:
    print(msg)
    sentData = input()
    client.sendall(formatText(sentData))

    

client.close()