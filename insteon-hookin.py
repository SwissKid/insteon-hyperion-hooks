#!/usr/bin/env python2
import time, socket, urllib2
#In secrets.py, have insteon_username = and insteon_password = 
from secrets import insteon_password, insteon_username
#Name your groups
groupnames = {'05': 'Games', '08': 'Media Room', '10': 'Movies'}
default_color = "[65,57,27]"
insteon_url = "http://192.168.1.160:25105/"
hyperion_url = "192.168.1.169"

i = 0
command = ""
device_id = ""
location = ""
brightness = ""
groupnum = ""
commandlist = []

password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
password_mgr.add_password(None,insteon_url,insteon_username,insteon_password)
handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(handler)
opener.open(insteon_url + "buffstatus.xml")
urllib2.install_opener(opener)

def send_hyperion( line ):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((hyperion_url, 19444))
	print "sending " + line
	s.send(line)
	s.close()
	
def color_on():
	line = '{"command": "color", "priority": 0, "color": ' + default_color + '}\n'
	send_hyperion(line)

def color_off():
	line = '{"command": "clear", "priority": 0}\n'
	send_hyperion(line)

def split_by_n( seq, n ):
    """A generator to divide a sequence into chunks of n units."""
    while seq:
        yield seq[:n]
        seq = seq[n:]
def inst_log( string ):
	print string
def error():
	print "WHAT HAPPENED ERROR"
def sceneCommand(scene, command):
	name = groupnames[scene]
	if name == "Games" or name == "Movies" :
		if command == "on":
			color_on()
		elif command == "off":
			color_off()
		print "Turning " +command + " backlight for " + name
	elif groupnames[scene] == "Media Room":
		color_off()
	
def processDeviceCommand():
	global i, device_id,command, brightness, location, groupnum, commandlist
	device_id = ''.join(map(str, commandlist[i:i+3]))
	i += 3
	if commandlist[i] == "05":
		i += 1 #Flag
		if commandlist[i] == "32": #Dual outlet On
			i += 1 #Group Byte
			command = "On"
			if commandlist[i] == "01":
				location = " Top Outlet "
			elif commandlist[i] == "02":
				location = " Bottom Outlet "
			else:
				error()
			i += 2
			inst_log( device_id + location + " turned " + command + brightness)
			#inst_log( str(i) + " with " + commandlist[i])
		elif commandlist[i] == "33": #Dual outlet Off
			i += 1 #Group Byte
			command = "Off"
			if commandlist[i] == "01":
				location = " Top Outlet "
			elif commandlist[i] == "02":
				location = " Bottom Outlet "
			else:
				error()
			i += 2
			inst_log( device_id + location + " turned " + command + brightness)
		elif commandlist[i] == "19": #Dual outlet Off
			inst_log( "Status Req" )
			i += 3
			
	else: 
		i += 1 #Flags Byte for not-05
		if commandlist[i] == "11": #On
			command = "on"
			##Include Command to execute a group thingy
		elif commandlist[i] == "13": #Off
			command = "off"
			##Include Command to execute a group thingy
		i += 1 #Command
		brightness = " To Brightness " + commandlist[i]
		inst_log( device_id + " turned " + command + brightness)
	
	
def processInsteonBuffer( buffstatus ):
	global i, device_id,command, brightness, location, groupnum, commandlist
	i = 0
	commandlist = list(split_by_n(buffstatus, 2))
	while i < len(commandlist):
		command = ""
		device_id = ""
		location = ""
		brightness = ""
		groupnum = ""
		#if i == 0 and commandlist[i] != "02":
		#	processDeviceCommand()
		if commandlist[i] == "A0": #end of string
			print "END OF STRING"
			break
		elif commandlist[i] == "02": #Start of new command
			i += 1
			if i == len(commandlist):
				inst_log( "WAT ITS THE END")
				inst_log( commandlist[i])
			elif commandlist[i] == "62": #Hub to PLM for device
				i += 1
				processDeviceCommand()
			elif commandlist[i] == "61": #Hub to PLM for Group
				i +=1
				groupnum = commandlist[i] #Group Number for Scene
				i +=1
				if commandlist[i] == "11": #On
					command = "on"
					##Include Command to execute a group thingy
				elif commandlist[i] == "13": #Off
					command = "off"
					##Include Command to execute a group thingy
				sceneCommand(groupnum, command)
				i += 2 # Blank
				if commandlist[i] == "06":
					i += 1
					inst_log( "made it")
				inst_log( groupnum + " turned " + command + brightness)
			elif commandlist[i] == "50": #Response from PLM
				#inst_log( ''.join(map(str,commandlist[i:i+10])))
				i += 10 #Forget about all the bytes
				inst_log( "Received and threw out response")
			elif commandlist[i] == "58": #Response from PLM From Group
				i += 2 #Forget about all the bytes
				inst_log( "Received and threw out response for group")
		elif commandlist[i] == "00":
			i += 1	
		else:
			inst_log( str(i) + " Failed: " + commandlist[i])
			i += 1
					



endstring = ""

while True:
	response = urllib2.urlopen('http://192.168.1.160:25105/buffstatus.xml')
	body = response.read()
	newstring = body[14:216]
	if newstring != endstring:
		endstring = newstring
		print endstring
		processInsteonBuffer(endstring)
		print "Processed Insteon Buffer"
	time.sleep(3)
