#!/usr/bin/env python

APPLICATION = "/home/david/Savage2/savage2.bin"
OPTIONS = ""
#OPTIONS = "; setconfig tournament"
HOST, PORT = "localhost", 4242
ENABLE_INET = False

import os
from sys import stdout
import signal
import readline, subprocess, re
import threading, SocketServer
from collections import deque
import curses
import ConfigParser

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

	def handle(self):

		print "\nConnection established by: %s\n" % self.client_address[0]
		Savage2ConsoleHandler.addChannel (self.onConsoleMessage)

		# while until user is gone.
		while (True):
			line = self.request.recv (1024);
			if (line == ''):
				break

			Savage2SocketHandler.put (line);
			Savage2SocketHandler.broadcast ();


		# clean up
		print "\nLost connection: %s" % self.client_address[0]
		Savage2ConsoleHandler.delChannel (self.onConsoleMessage)

	def onConsoleMessage (self, line):
		self.request.send (line + "\n")


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass


class Savage2Thread(threading.Thread):

	hack = 0
	process = None

	def run(self):
		self.launchDaemon ()

	def launchDaemon (self):
		Savage2SocketHandler.addChannel (self.onSocketMessage)
		Savage2DaemonHandler.addChannel (self.onDaemonMessage)
		self.process = subprocess.Popen ([APPLICATION, "Set host_dedicatedServer true%s" % OPTIONS], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
		print "Launched process(%s)" % self.process.pid 
		self.read ()

	def read(self):

		# annoying colors and stuff
		ansisequence = re.compile(r'\x1B\[[^A-Za-z]*[A-Za-z]|\x1b\([^A-Za-z]*[A-Za-z]|\x08')

		while (True):

			# read lines
			line = self.process.stdout.readline ();
			line = ansisequence.sub ('' , line).replace ("\t", "").replace ("\r" , "").replace ("\n" , "")
			line = line.replace ('^[[?1049h^[[1;52r^[[m^[(B^[[4l^[[?7h^[[?25l^[[H^[[2J^[[41d', '').replace ("^[)0" , '')

			# process is dead
			if line == "" and self.process.poll () is not None:
				break

			if (line == ">"):
				continue

			line = line.lstrip ('>')
			# broadcast
			Savage2ConsoleHandler.put (line)
			Savage2ConsoleHandler.broadcast ()

		self.clean ()
		print "Process dead?"

	def clean (self):
		print "IOError: %s(pid: %s) stdin is closed." % (APPLICATION, self.process.pid)
		Savage2SocketHandler.delChannel (self.onSocketMessage)
		Savage2DaemonHandler.delChannel (self.onDaemonMessage)
		self.launchDaemon ()

	def write(self, line):
		try:
			self.process.stdin.write (line + "\n")
		except IOError:
			self.clean ()

	def onSocketMessage (self, line):
		self.write (line)
	def onDaemonMessage (self, line):
		self.write (line)


class Savage2ConsoleHandler():

	def __init__(self):
		Savage2ConsoleHandler.queue = deque()
		Savage2ConsoleHandler.channel = []

	@staticmethod
	def addChannel (cb):
		Savage2ConsoleHandler.channel.append (cb)

	@staticmethod
 	def delChannel (cb):
		Savage2ConsoleHandler.channel.remove (cb)


	@staticmethod
	def put (line):
		Savage2ConsoleHandler.queue.append (line)

	@staticmethod
	def broadcast ():
		line = Savage2ConsoleHandler.get ()

		if (line is None):
			return;

		for cb in Savage2ConsoleHandler.channel:
			cb (line)

	@staticmethod
	def get():
		try:
			return Savage2ConsoleHandler.queue.popleft ()
		except:
			return None

class Savage2SocketHandler():

	def __init__(self):
		Savage2SocketHandler.queue = deque()
		Savage2SocketHandler.channel = []

	@staticmethod
	def addChannel (cb):
		Savage2SocketHandler.channel.append (cb)

	@staticmethod
 	def delChannel (cb):
		Savage2SocketHandler.channel.remove (cb)

	@staticmethod
	def put (line):
		Savage2SocketHandler.queue.append (line)

	@staticmethod
	def broadcast ():
		line = Savage2SocketHandler.get ()
		for cb in Savage2SocketHandler.channel:
			cb (line)

	@staticmethod
	def get():
		try:
			return Savage2SocketHandler.queue.popleft ()
		except:
			return None

class Savage2DaemonHandler():

	def __init__(self):
		Savage2DaemonHandler.queue = deque()
		Savage2DaemonHandler.channel = []

	@staticmethod
	def addChannel (cb):
		Savage2DaemonHandler.channel.append (cb)

	@staticmethod
 	def delChannel (cb):
		Savage2DaemonHandler.channel.remove (cb)

	@staticmethod
	def put (line):
		Savage2DaemonHandler.queue.append (line)

	@staticmethod
	def broadcast ():
		line = Savage2DaemonHandler.get ()
		for cb in Savage2DaemonHandler.channel:
			cb (line)

	@staticmethod
	def get():
		try:
			return Savage2DaemonHandler.queue.popleft ()
		except:
			return None

class ConsoleParser():

	filters = []

	def __init__(self):
		self.filters = dict({

			self.onRecievedAccountId : re.compile ('SGame: Recieved persistant stats for client (\d+) \(Account ID: (\d+)\)\.'),
			self.onConnect : re.compile ('Sv: New client connection: #(\d+), ID: (\d+), (\d+.\d+.\d+.\d+):(\d+)'),
			self.onSetName : re.compile ('Sv: Client #(\d+) set name to (\S+)'),
			self.onTeamChange : re.compile ('Sv: Client #(\d+) requested to join team: (\d)'),
			self.onMessage : re.compile ('Sv: \[(.*)\] (.*): (.*)'),
			self.onServerStatus : re.compile ('SGame: Server Status: Map\((.*)\) Timestamp\((\d+)\) Active Clients\((\d+)\) Disconnects\((\d+)\) Entities\((\d+)\) Snapshots\((\d+)\)'),
			self.onServerStatusResponse : re.compile ('Server Status: Map\((.*)\) Timestamp\((\d+)\) Active Clients\((\d+)\) Disconnects\((\d+)\) Entities\((\d+)\) Snapshots\((\d+)\)'),
			self.onDisconnect : re.compile ('SGame: Removed client #(\d+)'),
			self.onConnected : re.compile ('Sv: (\S+) has connected.'),
			self.onPlayerReady : re.compile ('Sv: Client #(\d+) is ready to enter the game'),
			self.onNewGame : re.compile ('NewGameStarted')
		})

	def onLineRecieved(self, line, dh):
		for handler in self.filters:

			filter = self.filters [handler]
			match = filter.match (line)

			if (match is not None):
				try:
					handler(match.groups () , Broadcast=dh)
				except Exception as e:
					print "Error in: %s: %s" % (repr(handler), e)

	#X Sv: New client connection: #203, ID: 8625, 83.226.95.135:51427
	def onConnect(self, *args, **kwargs):
		print "ON_CONNECT\n"
		print args
		print "\n"
		pass

	def onRecievedAccountId(self, *args, **kwargs):
		print "ON_RECIEVED_ACCOUNT_ID\n"
		print args
		print "\n"
		pass

	def onNewGame(self, *args, **kwargs):
		print "ON_NEW_GAME\n"
		print args
		print "\n"
		pass

	def onConnected(self, *args, **kwargs):
		print "ON_CONNECTED\n"
		print args
		print "\n"	
		pass

	def onPlayerReady(self, *args, **kwargs):
		print "ON_PLAYER_READY\n"
		print args
		print "\n"	
		pass

	#X Sv: Client #88 set name to Cicero23
	#def onSetName(self , clientId, name):
	def onSetName(self, *args, **kwargs):
		print "ON_SET_NAME\n"
		print args
		print "\n"
		pass

	#X SGame: Client #180 requested to join team: IDX
	#def onTeamChange (self, clientId, teamIdx):
	def onTeamChange (self, *args, **kwargs):
		print "ON_TEAM_CHANGE\n"
		print args
		print "\n"
		pass

	#X Sv: [TEAM 1] BeastSlayer`: need ammo
	#X Sv: [TEAM 2] BeastSlayer`: need ammo
	#X Sv: [ALL] bLu3_eYeS: is any 1 here ?
	#def onMessage (self, channel, name):
	def onMessage (self, *args, **kwargs):
		print "ON_MESSAGE\n"
		print args
		print "\n"
		pass

	# SGame: Server Status: Map(ss2010_6) Timestamp(69180000) Active Clients(9) Disconnects(160) Entities(1700) Snapshots(34671)
	#def onServerStatus(self, map, timestamp, activeClients, disconnects, entities, snapshots):
	def onServerStatus(self, *args, **kwargs):
		print "ON_SERVER_STATUS\n"
		print args
		print "\n"
		pass

	def onServerStatusResponse(self, *args, **kwargs):
		print "ON_SERVER_STATUS_RESPONSE\n"
		print args
		print "\n"
		pass

	# SGame: Removed client #195
	#def onDisconnect(self, clientId, message):
	def onDisconnect(self, *args, **kwargs):
		pass


	def cmd(self, string):
		Savage2DaemonHandler.put (string);
		Savage2DaemonHandler.broadcast ();

# Launches various threads, actual savage2 daemon and the inet server
import PluginsManager
class Savage2Daemon():

	parser = None
	server = None
	server_thread = None
	thread = None
	debug = ""
	dh = None

	def __init__(self):

		# Setup our broadcasters
		Savage2ConsoleHandler ()
		Savage2SocketHandler ()
		self.dh = Savage2DaemonHandler ()

		# Add callback's for messages
		Savage2ConsoleHandler.addChannel (self.onConsoleMessage)
		Savage2SocketHandler.addChannel (self.onSocketMessage)

		# Launch savage2 thread
		# this thread will run and handle savage2 dedicated server
		# relaunching it on savage2.bin exit.
		self.thread = Savage2Thread ()
		self.thread.daemon = True
		self.thread.start ()

	#print "\x1BE"
	def onConsoleMessage (self, line):
		print "(Debug)onConsoleMessage> %s" % line
	
		for plugin in PluginsManager.getEnabled (PluginsManager.ConsoleParser):
			plugin.onLineRecieved (line, self.dh)

		pass

	#print "(Debug)onSocketMessage> %s\n" % repr(line)
	def onSocketMessage (self, line):
		pass

	def disableServer(self):
		print "Shutting socket server down.\n"
		Savage2ConsoleHandler.delChannel (self.onConsoleMessage)
		Savage2SocketHandler.delChannel (self.onSocketMessage)
		self.server.shutdown ()

	def enableServer(self):
		self.server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)

		self.server_thread = threading.Thread(target=self.server.serve_forever)
		self.server_thread.setDaemon(True)
		self.server_thread.start ()

		ip, port = self.server.server_address
		print "Started daemon: %d\n" % port





# Main thread
if __name__ == "__main__":

	# Launch and enable our daemon/wrapper.
	savage2Daemon = Savage2Daemon ()

	if ENABLE_INET:
		savage2Daemon.enableServer ()


	os.system ('reset')
	print "\nLoading plugins..."
	PluginsManager.discover ()
	AutoPlugins = ConfigParser.ConfigParser ()
	AutoPlugins.read ('%s/plugins.ini' % os.path.dirname (os.path.realpath (__file__)))
	for (name, value) in AutoPlugins.items ('plugins'):

		if (value != "true"):
			continue

		if (PluginsManager.enable (name)):
			print "Plugin %s successfully loaded" % name

		else:
			print "Plugin %s not found" % name


	# Catch keyboard interrupts, while we run our main while.
	try:
		while True:

			# block till user input
			line = raw_input("")

			# get first word
			words = line.split (" ")
			if (words [0] == "exit"):
				break
			elif (words [0] == "plugins"):

				if (words [1] == "rediscover"):
					PluginsManager.discover ()

				elif (words [1] == "list"):
					print PluginsManager.list ()

				elif (words [1] == "reload" and len(words) > 2):
					PluginsManager.reload (words [2])

				elif (words [1] == "enable" and len(words) > 2):
					if (PluginsManager.enable (words [2])):
						print "Plugin %s has been enabled\n" % words [2]

				elif (words [1] == "disable" and len(words) > 2):
					if (PluginsManager.disable (words [2])):
						print "Plugin %s has been disabled\n" % words [2]
				else:
					print "\nMissing parameter. Syntax: plugins <command> <name>\n"


			elif (words [0] == "plugins" and len(words) <= 2):
				print "\nMissing parameter. Syntax: plugins <command>\n"

			# pass rest through the broadcaster
			else:
				Savage2DaemonHandler.put (line);
				Savage2DaemonHandler.broadcast ();
	
			pass
	except KeyboardInterrupt:
		pass

	# Clean.
	#savage2Daemon.disableServer ()
	print "Exit\n"
