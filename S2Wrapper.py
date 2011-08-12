#!/usr/bin/env python


import os
import sys
import time
import signal
import readline, subprocess, re
import threading, SocketServer
from collections import deque
import ConfigParser
import stty
from threading import Timer



class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

	def handle(self):

		print "\nConnection established by: %s\n" % self.client_address[0]
		Savage2ConsoleHandler.addChannel (self.onConsoleMessage)

		# while until user is gone.
		while (True):
			line = self.request.recv (1024);
			if (line == ''):
				break

			Savage2SocketHandler.broadcast(line)

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
	alive = False
	def __init__(self, config):
		threading.Thread.__init__(self)
		self.config = config
		
	def run(self):
		self.launchDaemon ()

	def launchDaemon (self):
		Savage2SocketHandler.addChannel (self.onSocketMessage)
		Savage2DaemonHandler.addChannel (self.onDaemonMessage)

		config = self.config
		args = [config['exec']]
		if config['args']:
			args += [config['args']]
		env = [config['env']]

		termold = stty.getSize()
		termcfg = (int(config['term_x']), int(config['term_y']))
		termnew = (
			termcfg[0] if termcfg[0] > 0 else termold[0],
			termcfg[1] if termcfg[1] > 0 else termold[1] )
		stty.setSize(termnew)

		print("starting: %s" % (args))
		try:
			self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
			#self.process = subprocess.Popen(args, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
			print("[%s] has started successfully" % (self.process.pid))
			self.alive = True
			# give some time for process to read new tty size
			time.sleep(0.1)
		finally:
			# return old size in any case
			stty.setSize(termold)

		if not self.process:
			return
		#self.pingAlive()
		#self.checkAlive()
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
			#if line == "" and self.process.poll () is not None:
			if self.process.poll () is not None:
				break

			if (line == ">"):
				continue

			line = line.lstrip ('>')
			#if it catches the ALIVE statement, set the local variable True
			active = re.match('^ALIVE', line)
			if active:
				self.alive = True
			#ignore all the crap that clutters up the output
			ignore = re.match('^Resource: |(SGame:)?\s?Spawned new |(SGame:)?\s?Adding Building |Error: CClientConnection|(\d+)$', line)
			if ignore: 
				continue
			else:
				# broadcast
				Savage2ConsoleHandler.broadcast(line)

			
		self.clean ()
		print "Process dead?"

	def clean (self):
		print("IOError: [%d] %s stdin is closed." % (self.process.pid, self.config['exec']))
		Savage2SocketHandler.delChannel (self.onSocketMessage)
		Savage2DaemonHandler.delChannel (self.onDaemonMessage)
		# don't go crazy spawning process too fast, sleep some instead
		time.sleep(1.0)
		if self.config['once'] == "true":
			return
		self.launchDaemon()

	def write(self, line):
		try:
			self.process.stdin.write (line + "\n")
		except IOError:
			self.clean ()

	def onSocketMessage (self, line):
		self.write (line)
	def onDaemonMessage (self, line):
		self.write (line)

	def checkAlive (self):
		
		print ('Is process alive: %s' % (self.alive))
		if self.process.poll () is not None:
			self.clean()
			return

		if self.alive == False:
			self.process.kill ()
			self.clean()
			return

		
		r = threading.Timer(60.0, self.checkAlive)
		r.start()

		self.alive = False
		

	def pingAlive (self):
				
		Savage2SocketHandler.broadcast("echo ALIVE")
		
		r = threading.Timer(30.0, self.pingAlive)
		r.start()
		
class Savage2ConsoleHandler:

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
	def broadcast(line=None):
		if line:
			Savage2ConsoleHandler.put(line)
		for line in Savage2ConsoleHandler.queue:
			for cb in Savage2ConsoleHandler.channel:
				cb(line)
		Savage2ConsoleHandler.queue.clear()


class Savage2SocketHandler:

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
	def broadcast(line=None):
		if line:
			Savage2SocketHandler.put(line)
		for line in Savage2SocketHandler.queue:
			for cb in Savage2SocketHandler.channel:
				cb(line)
		Savage2SocketHandler.queue.clear()


class Savage2DaemonHandler:

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
	def broadcast(line=None):
		if line:
			Savage2DaemonHandler.put(line)
		for line in Savage2DaemonHandler.queue:
			for cb in Savage2DaemonHandler.channel:
				cb(line)
		Savage2DaemonHandler.queue.clear()


class ConsoleParser:

	filters = []

	def __init__(self):
		self.filters = dict({
			# listed in order of appearance, likeliness and sanity
			self.onServerStatus  : re.compile ('SGame: Server Status: Map\((.*?)\) Timestamp\((\d+)\) Active Clients\((\d+)\) Disconnects\((\d+)\) Entities\((\d+)\) Snapshots\((\d+)\)'),
			self.onServerStatusResponse : re.compile ('Server Status: Map\((.*?)\) Timestamp\((\d+)\) Active Clients\((\d+)\) Disconnects\((\d+)\) Entities\((\d+)\) Snapshots\((\d+)\)'),
			self.onConnect     : re.compile ('Sv: New client connection: #(\d+), ID: (\d+), (\d+\.\d+\.\d+\.\d+):(\d+)'),
			self.onSetName     : re.compile ('Sv: Client #(\d+) set name to (\S+)'),
			self.onPlayerReady : re.compile ('Sv: Client #(\d+) is ready to enter the game'),
			self.onAccountId   : re.compile ('(?:Sv: )*?Getting persistant stats for client (\d+) \(Account ID: (\d+)\)\.'),
			self.onStartServer : re.compile ('^K2 Engine start up.*'),
			self.onNewGameStarted : re.compile ('NewGameStarted'),
			#self.onConnected   : re.compile ('Sv: (\S+) has connected.'),
			self.onMessage     : re.compile ('Sv: \[(.+?)\] ([^\s]+?): (.*)'),
			self.onDisconnect  : re.compile ('SGame: Removed client #(\d+)'),
			self.onPhaseChange : re.compile ('(?:SGame: |Sv: )*?SetGamePhase\(\): (\d+) start: (\d+) length: (\d+) now: (\d+)'),
			self.onTeamChange  : re.compile ('(?:SGame: |Sv: )*?Client #(\d+) requested to join team: (\d+)'),
			self.onHasKilled   : re.compile ('Sv: (\S+) has been killed by (\S+)'),
			self.onUnitChange  : re.compile ('(?:SGame:|Sv:)?.?Client #(\d+) requested change to: (\S+)'),
			self.onCommResign  : re.compile ('SGame: (\S+) has resigned as commander.'),
			self.onMapReset    : re.compile ('.*\d+\.\d+\s{3, 6}'),
			# custom filters
			self.onItemTransaction : re.compile ('Sv: ITEM: Client (\d+) (\S+) (.*)'),
			self.onRefresh : re.compile ('^refresh'),
			self.onRefreshTeams : re.compile ('CLIENT (\d+) is on TEAM (\d+)'),
			self.onTeamCheck : re.compile ('^SERVER-SIDE client count, Team 1 (\d+), Team 2 (\d+)'),
			self.onRetrieveIndex : re.compile ('Sv: Client (\d+) index is (\d+). ACTION: (\S+)'),
			self.onListClients : re.compile ('^.* #(\d+) .*: (\d+\.\d+\.\d+\.\d+).*\\"(\S+)\"'),
			self.onGetLevels : re.compile ('^CLIENT (\d+) is LEVEL (\d+)'),
			self.RegisterStart : re.compile ('^STARTTOURNEY'),
			self.getNextDuel : re.compile ('^NEXTDUELROUND'),
			self.waitForPlayer : re.compile ('.*MISSING: (\S+)'),
			self.onDeath : re.compile('SGame: DUEL: (\d+) defeated (\d+)'),
			self.onFighterRemoved : re.compile('SGame: REMOVED PLAYER (\d+) TEAM (\d+)'),
			self.getServerVar : re.compile('^SERVERVAR: (\S+) is (.*)'),
			self.getHashCheck : re.compile('Sv: HACKCHECK ClientNumber: (\d+), AccountID: (\d+), Hashcheck result: (\S+)'),
			self.getMatchID   : re.compile('SGame: Authenticated server successfully, stats will be recorded this game. Match ID: (\d+), Server ID: (\d+)'),
			self.getEvent : re.compile('(?:SGame: |Sv: )*?EVENT (\S+) (\S+) on (\S+) by (\S+) at (\d+\.\d+) (\d+\.\d+) (\d+\.\d+)'),
			self.mapDimensions : re.compile('Error: CWorld::GetTerrainHeight\(\) - Coordinates are out of bounds'),
			self.onScriptEvent : re.compile('(?:SGame: |Sv: )*?SCRIPT Client (\d+) (\S+) with value (\S+)')
		})

	def onLineReceived(self, line, dh):
		for handler in self.filters:
			filter = self.filters[handler]
			match = filter.match(line)
			if not match:
				continue

			try:
				handler(*match.groups(), Broadcast=dh)
			except Exception, e:
				print("Error in: %s: %s" % (repr(handler), e))


	# SGame: Server Status: Map(ss2010_6) Timestamp(69180000) Active Clients(9) Disconnects(160) Entities(1700) Snapshots(34671)
	def onServerStatus(self, *args, **kwargs):
		pass
	def onServerStatusResponse(self, *args, **kwargs):
		pass

	#X Sv: New client connection: #203, ID: 8625, 83.226.95.135:51427
	def onConnect(self, *args, **kwargs):
		pass

	#X Sv: Client #88 set name to Cicero23
	def onSetName(self, *args, **kwargs):
		pass

	def onPlayerReady(self, *args, **kwargs):
		pass

	def onAccountId(self, *args, **kwargs):
		pass

	def onStartServer(self, *args, **kwargs):
		pass

	def onNewGameStarted(self, *args, **kwargs):
		pass
	#def onConnected(self, *args, **kwargs):
	#	pass

	#X Sv: [TEAM 1] BeastSlayer`: need ammo
	#X Sv: [TEAM 2] BeastSlayer`: need ammo
	#X Sv: [ALL] bLu3_eYeS: is any 1 here ?
	def onMessage(self, *args, **kwargs):
		pass

	# SGame: Removed client #195
	def onDisconnect(self, *args, **kwargs):
		pass

	def onPhaseChange(self, *args, **kwargs):
		pass

	#X SGame: Client #180 requested to join team: IDX
	def onTeamChange(self, *args, **kwargs):
		pass

	def onHasKilled(self, *args, **kwargs):
		pass

	def onUnitChange(self, *args, **kwargs):
		pass

	def onCommResign(self, *args, **kwargs):
		pass
	def onMapReset(self, *args, **kwargs):
		print("SHUFFLE HAS BEEN CALLED, now DO SOMETHING")
		pass

		
	# custom filters - TO BE REMOVED
	def onItemTransaction(self, *args, **kwargs):
		pass
	def onRefresh(self, *args, **kwargs):
		pass
	def onTeamCheck(self, *args, **kwargs):
		pass
	def onRefreshTeams(self, *args, **kwargs):
		pass
	def onRetrieveIndex(self, *args, **kwargs):
		pass
	def onListClients(self, *args, **kwargs):
		pass
	def onGetLevels(self, *args, **kwargs):
		pass
	def RegisterStart(self, *args, **kwargs):
		pass
	def getNextDuel(self, *args, **kwargs):
		pass
	def waitForPlayer(self, *args, **kwargs):
		pass
	def onDeath(self, *args, **kwargs):
		pass
	def onFighterRemoved(self, *args, **kwargs):
		pass
	def getServerVar(self, *args, **kwargs):
		pass
	def getHashCheck(self, *args, **kwargs):
		pass
	def getMatchID(self, *args, **kwargs):
		pass
	def getEvent(self, *args, **kwargs):
		pass
	def mapDimensions(self, *args, **kwargs):
		pass
	def onScriptEvent(self, *args, **kwargs):
		pass
	def cmd(self, string):
		Savage2DaemonHandler.broadcast(string)


# Launches various threads, actual savage2 daemon and the inet server
import PluginsManager
class Savage2Daemon:

	parser = None
	server = None
	server_thread = None
	thread = None
	debug = ""
	dh = None

	def __init__(self, config):
		self.config = config

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
		self.thread = Savage2Thread(dict(config.items('core')))
		self.thread.daemon = True
		self.thread.start ()

	#print "\x1BE"
	def onConsoleMessage (self, line):
		print "onConsoleMessage> %s" % line
	
		for plugin in PluginsManager.getEnabled (PluginsManager.ConsoleParser):
			plugin.onLineReceived (line, self.dh)

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
		config = self.config
		addr = (config.get('inet', 'listen'), config.getint('inet', 'port'))
		self.server = ThreadedTCPServer(addr, ThreadedTCPRequestHandler)

		self.server_thread = threading.Thread(target=self.server.serve_forever)
		self.server_thread.setDaemon(True)
		self.server_thread.start ()

		ip, port = self.server.server_address
		print "Started daemon: %d\n" % port



def config_exists(name, suggestion=None):
	if os.path.isfile(name):
		return True
	msg = "ERROR: File not found: %s\n" % (name)
	sys.stderr.write(msg + suggestion + "\n")
	return False

def config_dump(config):
	for sect in config.sections():
		print(sect)
		for item in config.items(sect):
			print(item)
	return

def config_read(cfgs, config = None):
	if not config:
		config = ConfigParser.ConfigParser()

	print("config_read(): %s" % (cfgs))
	if config.read(cfgs):
		#config_dump(config)
		pass

	return config

def config_write(filename, config):
	print("config_write(): %s" % (filename))
	with open(os.path.expanduser(filename), "wb") as f:
		config.write(f)
	return



# Main thread
if __name__ == "__main__":
	# prepare paths and names
	path_install = os.path.dirname(os.path.realpath(__file__))
	path_plugins = os.path.join(path_install, "plugins")
	conf_def = "default.ini"
	conf_loc = "s2wrapper.ini"
	#dir_mod = "server"

	# read default config
	cfgdef = os.path.join(path_install, conf_def)
	if not config_exists(cfgdef, "Please get '%s' from upstream :)" % (conf_def)):
		sys.exit(1)
	config = config_read(cfgdef)

	# read local config
	path_home = config.get('core', 'home')
	if path_home == ".":
		path_home = path_install
	else:
		path_home = os.path.expanduser(path_home)
	#path_home = os.path.join(path_home, dir_mod)
	cfgloc    = os.path.join(path_home, conf_loc)
	if not config_exists(cfgloc, "Read '%s' for instructions" % (conf_def)):
		sys.exit(1)
	config_read(cfgloc, config)

	PluginsManager.discover(path_plugins)

	# enable listed plugins
	for name in config.options('plugins'):
		if name == 'admin':
			PluginsManager.enable(name)
			continue
		if config.getboolean('plugins', name):
			PluginsManager.enable(name)
		
	# write local config
	#config_write(cfgloc, config)


	# reset our terminal
	os.system('reset')

	# launch daemon
	daemon = Savage2Daemon(config)
	# enable inet server
	if config.getboolean('inet', 'enable'):
		daemon.enableServer()


	# Catch keyboard interrupts, while we run our main while.
	try:
		while True:
			# block till user input
			try:
				line = raw_input("")
			except EOFError:
				print("%s: caught EOF, what should i do?" % (__name__))
				continue

			# get command and argument as 2 strings
			args = line.strip().split(None, 1)
			if not args:
				continue
			arg = args[1] if (len(args) > 1) else None
			cmd = args[0]

			if cmd == "exit":
				break

			if cmd == "plugins":
				if not arg:
					print("Syntax: %s <command>" % (cmd))
					continue

				args = arg.split(None, 1)
				arg  = args[1] if (len(args) > 1) else None
				cmd2 = args[0]
				if not arg:
					if   cmd2 == "discover":
						PluginsManager.discover()
					elif cmd2 == "list":
						print("\n".join(PluginsManager.list()))
					else:
						print("%s: %s: unknown command" % (cmd, cmd2))
				else:
					if   cmd2 == "reload":
						PluginsManager.reload(arg)
					elif cmd2 == "enable":
						PluginsManager.enable(arg)
					elif cmd2 == "disable":
						PluginsManager.disable(arg)
					else:
						print("%s: %s: unknown command" % (cmd, cmd2))

			# pass rest through the broadcaster
			else:
				Savage2DaemonHandler.broadcast(line)

			pass
	except KeyboardInterrupt:
		print("%s: caught SIGINT" % (__name__))
		pass

	# Clean.
	#daemon.disableServer()
	print("%s: exiting..." % (__name__))
