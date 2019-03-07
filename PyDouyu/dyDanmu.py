



import requests
import socket
import sys
import struct
import threading
import time
import re

douyutv_url = "openbarrage.douyutv.com:8601"


io_lock = threading.Lock()
g_timer = []

def killTimer():
	global g_timer
	for ltimer in g_timer:
		ltimer.cancel()
	g_timer = []
	
def GetTimeStamp():
	return int(round(time.time()*1000))
	
class ClassPack:
	pass

def IsServerMsg(response):
	pack = ClassPack()
	pack.rawlen,pack.length,pack.megtype,pack.enum,pack.rnum = struct.unpack("<IIHBB",response[0:12])
	if pack.rawlen == pack.length and pack.megtype == 690:
		return pack
	return False
	

	
def SendDouyuMrkl(socket):	
	dictMrkl = {
		"type":"mrkl",
	}
	
		# timeStamp = int(round(time.time()*1000))
		#dictMrkl = {	"type":"keeplive","tick":"%s"%timeStamp }				
	msgMrkl = douyuMakeMsg(dictMrkl)
	while 1:
		time.sleep(45)
		with io_lock:
			socket.send(msgMrkl)	
			print("Client ：sendMrkl")

			
	
class douyuDanmu:
	def __init__(self,roomid):
		self.socket = socket.socket(
			socket.AF_INET, socket.SOCK_STREAM) 
		self.host = "openbarrage.douyutv.com"
		self.port = 8601
		self.roomid = roomid

	def send(self,msg):
		self.send(msg)
		
	def recv(self):
		with io_lock:
			socket = self.socket
			data = socket.recv(1024)		
			if not data:
				return None
			return data
		
	def joingroup(self):
		sclient = self.socket
		dictJoinGroup ={
			"type":"joingroup",
			"rid":str(self.roomid),
			"gid":"-9999"
		}
		
		msgJoinGroup = douyuMakeMsg(dictJoinGroup)
		sclient.send(msgJoinGroup)	
		
		self.MrklTimer = threading.Thread(target=SendDouyuMrkl,args=[self.socket ,],daemon = True)
		self.MrklTimer.setDaemon(True)
		self.MrklTimer.start()

		
	def login(self):
		sclient = self.socket
		sclient.connect((self.host, self.port))
		dictLogin = {
			"type":"loginreq",
			"roomid":str(self.roomid),
		}

		msgLogin = douyuMakeMsg(dictLogin)
		sclient.send(msgLogin)			

	def logout(self):
		self.MrklTimer.cancel()
		#g_timer.remove(self.MrklTimer)
		sclient = self.socket
		dictLogout = {
			"type":"logout",
		}
		msgLogout = douyuMakeMsg(dictLogout)
		sclient.send(msgLogout)
		
		
	def sendMrkl(self):	
		with io_lock:
			sclient = self.socket
			
			dictMrkl = {
				"type":"mrkl",
			}
					
			msgMrkl = douyuMakeMsg(dictMrkl)
			sclient.send(msgMrkl)	
			
		
def douyuMakeMsg(dict):
	msgtype = 689
	msgstr = ""
	for k in dict:
		msgstr += k + "@=" + dict[k] +"/"
	msgstr +="\0"
	msglen = 8 + len(msgstr) 
	#Msg = bytes(msglen)
	Msg = struct.pack("<IIHBB",msglen,msglen,msgtype,0,0) + bytes(msgstr,encoding = "utf-8")
	return Msg
	
def GetResMsg(response):
	reslen = len(response)	
	zeropos = 0
	try :
		zeropos = response[12:].index(0) +12	
	except ValueError as e:
		return []

	ret_data = []
	if	zeropos > 12 :
		ret_data.append(response[12:zeropos+1])
		try :
			resnext = response[zeropos+1:]
		except ValueError as e:
			return ret_data
		else:
			ret_data += GetResMsg(resnext)
		
	return ret_data
	
def Res2Dict(resmsg):
	msgsrc = ""
	try:
		msgsrc = resmsg.decode("utf-8","ignore")
	except UnicodeDecodeError as e:
		err = "%s"%e
		pos = re.match("\d+",err[err.find("position")+9:])[0]		
		print("response.msg.decode.error:\n%s\n%s" %(resmsg,e))
		print("pos value : 0x%x"%resmsg[int(pos)])
		#killTimer()		
		exit(-1)	
	
	msgArr = msgsrc.split("/")
	msgdict = {}
	for l in msgArr:
		kv = l.split("@=")
		if len(kv) == 2:
			key = kv[0].replace("@S","/").replace("@A","@")
			value = kv[1].replace("@S","/").replace("@A","@")
			msgdict[key] = value
	
	return msgdict
	
def douyuGetResMsg(response):
	reslen = len(response)
	if reslen < 12:
		print("error：",response)
		return None
		
	len1,len2,megtype,enum,rnum = struct.unpack("<IIHBB",response[0:12])	
	
	if megtype != 690:
		return None

	liMsg = GetResMsg(response)
	
	msgDictList = []
	if len(liMsg) > 0:			
		for msg in liMsg:
			dict = Res2Dict(msg)
			if not dict: continue
			msgDictList.append(dict)
		return msgDictList
	return None
		
def douyuRecv(socket):
	data = socket.recv(4)
	if not data or len(data) ==0 :
		return None
	msglen = struct.unpack("<I",data[0:4])[0]
	if msglen:
		data += socket.recv(msglen)
		return data
	return None
	
def PrintChatmsg(client,msgdict):
	if msgdict and "type" in msgdict:
		if msgdict["type"] == "chatmsg":
			print("%s : %s"%(msgdict["nn"],msgdict["txt"]))
		#elif msgdict["type"] == "mrkl":
			#print("发送心跳...")
		#	client.sendMrkl()
		elif msgdict["type"] == "uenter":
			print("%s : %s"%("进入直播间",msgdict["nn"]))
		elif msgdict["type"] == "rss":
			if "ss" in msgdict :
				client.status.ss = int(msgdict["ss"])
		#else:
		#	print(msgdict["type"])
	
	
def main(roomid):
	danmuclient = douyuDanmu(roomid)
	danmuclient.login()
	danmuclient.joingroup()
	while 1:
		data = danmuclient.recv()
		if data == None : continue
		msgdict = douyuGetResMsg(data)
		if msgdict == None : continue
		for msg in msgdict:
			PrintChatmsg(danmuclient,msg)
	danmuclient.logout()

	
#1662839
if __name__ == '__main__':
	print(sys.argv[1])
	main(int(sys.argv[1]))
	



