# -*- coding: utf-8 -*-
# Auto-update incorporation, yet another last test
import re
import math
import time
import ConfigParser
import threading
import random
import os
import PluginsManager
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler
from operator import itemgetter
from numpy import median
import urllib2
import subprocess

class admin(ConsolePlugin):
	VERSION = "1.1.1"
	playerlist = []
	adminlist = []
	banlist = []
	ipban = []
	PHASE = 0
	CONFIG = None
	UPDATE = True
	NEEDRELOAD = False

	def onPluginLoad(self, config):
		
		self.ms = MasterServer ()
		self.CONFIG = config
		ini = ConfigParser.ConfigParser()
		ini.read(config)
		
		for (name, value) in ini.items('admin'):
			self.adminlist.append({'name': name, 'level' : value})
		for (name, value) in ini.items('ipban'):
			self.ipban.append(name)	
		
		pass
		
	def reload_config(self):
		
        	self.adminlist = []
       		self.ipban = []
                ini = ConfigParser.ConfigParser()
                ini.read(self.CONFIG)

                for (name, value) in ini.items('admin'):
                	self.adminlist.append({'name': name, 'level' : value})
                for (name, value) in ini.items('ipban'):
                	self.ipban.append(name)	

	def reload_plugins(self):
	
		config = os.path.realpath(os.path.dirname (os.path.realpath (__file__)) + "/../s2wrapper.ini")
		print config
		ini = ConfigParser.ConfigParser()
		ini.read(config)
		for name in ini.options('plugins'):
			if name == 'admin':
				PluginsManager.reload(name)
				continue
			if ini.getboolean('plugins', name):
				PluginsManager.reload(name)
			
	def onStartServer(self, *args, **kwargs):
				
		self.playerlist = []
		self.banlist = []	

	def getPlayerByClientNum(self, cli):

		for client in self.playerlist:
			if (client['clinum'] == cli):
				return client

	def getPlayerByName(self, name):

		for client in self.playerlist:
			if (client['name'].lower() == name.lower()):
				return client

	def onConnect(self, *args, **kwargs):
		
		id = args[0]
		ip = args[2]
		
		for each in self.ipban:
			if each == ip:
				reason = "You are banned from this server."
				kwargs['Broadcast'].broadcast("kick %s \"%s\"" % (id, reason))
				return

		reason = "An administrator has removed you from this server. You may rejoin the server after the current game ends."
		
		for each in self.banlist:
			if each == ip:
				kwargs['Broadcast'].broadcast(\
					"Kick %s \"%s\"" % (id, reason))

		for client in self.playerlist:
			if (client['clinum'] == id):
				return
		
		self.playerlist.append ({'clinum' : id,\
					 'acctid' : 0,\
					 'name' : 'X',\
					 'ip' : ip,\
					 'team' : 0,\
					 'sf' : 0,\
					 'active' : False,\
					 'level' : 0,\
					 'admin' : False,\
					 'commander' : False})
	
	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client ['active'] = False

	def onSetName(self, *args, **kwargs):
		
		cli = args[0]
		playername = args[1]
		client = self.getPlayerByClientNum(cli)
		client ['name'] = playername
					
	def onAccountId(self, *args, **kwargs):
		cli = args[0]
		id = args[1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		level = int(stats['level'])
		sf = int(stats['sf'])
					
		client = self.getPlayerByClientNum(cli)
		client['sf'] = sf
		client['level'] = level
		client['active'] = True

		if self.isAdmin(client, **kwargs):
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^cYou are registered as an administrator. Send the chat message: ^rhelp ^cto see what commands you can perform."\
			 % (cli))
			client['admin'] = True

		if self.isSuperuser(client, **kwargs):
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^cYou are registered as superuser on this server. You can send console commands with chat message: ^rsudo <command>."\
			 % (cli))

	def isAdmin(self, client, **kwargs):
		admin = False
		
		for each in self.adminlist:
			if client['name'].lower() == each['name']:
				admin = True
		
		return admin

	def isSuperuser(self, client, **kwargs):
		superuser = False

		for each in self.adminlist:
			if client['name'].lower() == each['name']:
				if each['level'] == 'super':
					superuser = True
		
		return superuser

	def onMessage(self, *args, **kwargs):
		
		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
		clinum = client['clinum']
		admin = self.isAdmin(client, **kwargs)
		superuser = self.isSuperuser(client, **kwargs)

		request = re.match("request admin", message, flags=re.IGNORECASE)
		if request:
			for each in self.playerlist:
				if each['active'] and each['admin']:
					kwargs['Broadcast'].broadcast("SendMessage %s Admin present: ^y%s" % (client['clinum'], each['name']))

		
		#ignore everything else if it isn't from admin
		if not admin:
			return

		#Pass to superCommand if the player is a superuser
		if superuser:
			self.superCommand(message, **kwargs)
		
		#Attempt to recover proper player number
		

		restart = re.match("admin restart", message, flags=re.IGNORECASE)
		shuffle = re.match("admin shuffle", message, flags=re.IGNORECASE)
		kick = re.match("admin kick (\S+)", message, flags=re.IGNORECASE)
		ban = re.match("admin ban (\S+)", message, flags=re.IGNORECASE)
		slap = re.match("admin slap (\S+)", message, flags=re.IGNORECASE)
		changeworld = re.match("admin changeworld (\S+)", message, flags=re.IGNORECASE)
		help = re.match("help", message, flags=re.IGNORECASE)
		balance = re.match("admin balance", message, flags=re.IGNORECASE)
		getbalance = re.match("admin get balance", message, flags=re.IGNORECASE)
		reportbal = re.match("admin report balance", message, flags=re.IGNORECASE)

		if restart:
			#restarts server if something catastrophically bad has happened
			kwargs['Broadcast'].broadcast("restart")

		if shuffle:
			#artificial shuffle vote
			if self.PHASE != 5:
				kwargs['Broadcast'].broadcast(\
					"SendMessage %s Cannot shuffle until the game has started!"\
					 % (client['clinum']))
				return
			
			kwargs['Broadcast'].broadcast("SendMessage -1 %s has shuffled the game." % (name))
			self.listClients(**kwargs)	
			shufflethread = threading.Thread(target=self.onShuffle, args=(), kwargs=kwargs)
			shufflethread.start()

		if kick:
			#kicks a player from the server
			reason = "An administrator has removed you from the server, probably for being annoying"
			kickclient = self.getPlayerByName(kick.group(1))
			kwargs['Broadcast'].broadcast(\
				"Kick %s \"%s\""\
				 % (kickclient['clinum'], reason))
			
		if ban:
			#kicks a player from the server and temporarily bans that player's IP till the game is over
			reason = "An administrator has banned you from the server. You are banned till this game is over."
			kickclient = self.getPlayerByName(ban.group(1))
			kwargs['Broadcast'].broadcast(\
				"Kick %s \"%s\"" \
				 % (kickclient['clinum'], reason))
			self.banlist.append(kickclient['ip'])

		if slap:
			#slap will move a player x+100, y+200 to get them off of a structure
			
			slapclient = self.getPlayerByName(slap.group(1))
			kwargs['Broadcast'].broadcast(\
				"set _slapindex #GetIndexFromClientNum(%s)#;\
				 set _sx #GetPosX(|#_slapindex|#)#; set _sy #GetPosY(|#_slapindex|#)#; set _sz #GetPosZ(|#_slapindex|#)#;\
				 SetPosition #_slapindex# [_sx + 200] [_sy + 200] #_sz#;\
				 SendMessage %s ^cAn adminstrator has moved you for jumping on buildings. YOU WILL BE BANNED if this action persists"\
				 % (slapclient['clinum'], slapclient['clinum']))
			

		if changeworld:
			#change the map
			kwargs['Broadcast'].broadcast(\
				"changeworld %s"\
				 % (changeworld.group(1)))

		
		if balance:
			if self.PHASE != 5:
				kwargs['Broadcast'].broadcast(\
					"SendMessage %s Cannot balance if the game has not started!"\
					 % (client['clinum']))
				return

			kwargs['Broadcast'].broadcast("SendMessage -1 %s has balanced the game." % (name))
			self.listClients(**kwargs)
			#balancethread = threading.Thread(target=self.onBalance, args=clinum, kwargs=kwargs)
			balancethread = threading.Thread(target=self.onBalance, args=(), kwargs=kwargs)
			balancethread.start()
			

		if getbalance:
			self.listClients(**kwargs)
			balancethread = threading.Thread(target=self.getBalance, args=clinum, kwargs=kwargs)
			balancethread.start()


		if reportbal:
			self.listClients(**kwargs)
			balancethread = threading.Thread(target=self.reportBalance, args=(), kwargs=kwargs)
			balancethread.start()

		self.logCommand(client['name'],message)

		if help:
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s All commands on the server are done through server chat. All commands are logged to prevent you from abusing them.The following are commands and a short description of what they do."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^radmin restart ^whard reset of the server. ONLY use in weird cases."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^radmin shuffle ^wwill shuffle the game and set to previous phase."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^radmi kick playername ^wwill remove a player from the server."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^radmin ban playername ^wwill remove a player from the server and ban that IP address till the end of the game."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^radmin slap playername ^wwill move the player. Use to get them off of structures if they are exploiting."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^radmin changeworld mapname ^wwill change the map to the desired map."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^radmin balance ^wwill move two players to achieve balance."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^radmin get balance ^wwill report avg. and median SF values for the teams as well as a stack value."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^radmin report balance ^wwill send a message to ALL players that has the avg. and median SF values."\
				 % (client['clinum']))

	def getBalance(self, clinum, **kwargs):
		time.sleep(1)
		teamone = []
		teamtwo = []

		#populate current team lists:
		for each in self.playerlist:
			if not each['active']:
				continue
			if each['team'] == 1:
				teamone.append(each)
			if each['team'] == 2:
				teamtwo.append(each)
		
		teamonestats = self.getTeamInfo(teamone)
		teamtwostats = self.getTeamInfo(teamtwo)
		stack = self.evaluateBalance(teamone, teamtwo)
		kwargs['Broadcast'].broadcast(\
		"SendMessage %s ^y Team One (%s players) Avg. SF is ^r%s^y median is ^r%s^y, Team Two (%s players) Avg. SF is ^r%s^y median is ^r%s. Stack value: %s" \
		 % (clinum, teamonestats['size'], teamonestats['avg'], teamonestats['median'], teamtwostats['size'], teamtwostats['avg'], teamtwostats['median'], stack))

	def reportBalance(self, **kwargs):
		time.sleep(1)
		teamone = []
		teamtwo = []
		#populate current team lists:
		for each in self.playerlist:
			if not each['active']:
				continue
			if each['team'] == 1:
				teamone.append(each)
			if each['team'] == 2:
				teamtwo.append(each)

		teamonestats = self.getTeamInfo(teamone)
		teamtwostats = self.getTeamInfo(teamtwo)
		stack = self.evaluateBalance(teamone, teamtwo)
		kwargs['Broadcast'].broadcast(\
		"SendMessage -1 ^y Team One (%s players) Avg. SF is ^r%s^y median is ^r%s^y, Team Two (%s players) Avg. SF is ^r%s^y median is ^r%s. Stack value: %s" \
		 % (teamonestats['size'], teamonestats['avg'], teamonestats['median'], teamtwostats['size'], teamtwostats['avg'], teamtwostats['median'], stack))

	def superCommand(self, message, **kwargs):
		#This allows superuser to issue any console command
		supercommand = re.match("sudo (.*)", message, flags=re.IGNORECASE)
		
		if supercommand:
			kwargs['Broadcast'].broadcast("%s" % (supercommand.group(1)))
		
				 
	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		self.PHASE = phase
		
		if (phase == 7):
			self.banlist = []	
			for each in self.playerlist:
				each['team'] = 0
				each['commander'] = False
					
		if (phase == 6):
			if self.UPDATE:
			#fetch admin list and reload at the start of each game
				updatethread = threading.Thread(target=self.update, args=(), kwargs=kwargs)
				updatethread.start()	
			#check if server is empty after 2 minutes		
				pluginthread = threading.Thread(target=self.pluginreload, args=(), kwargs=kwargs)
				pluginthread.start()
		
		if (phase == 4):
			kwargs['Broadcast'].broadcast("listclients")

	def update(self, **kwargs):
		
		'''
		response = urllib2.urlopen('http://188.40.92.72/admin.ini')
		adminlist = response.read()
		
		f = open(self.CONFIG, 'w')
		f.write(adminlist)
		f.close
		f.flush()
		os.fsync(f.fileno())
		self.reload_config()
		
		'''	
		if self.NEEDRELOAD:
			self.pluginreload(**kwargs)
			return

		#Update the wrapper
		try:
			gitpath = os.path.realpath(os.path.dirname (os.path.realpath (__file__)) + "/../.git")
			command = ["git","--git-dir",gitpath,"pull"]
			output = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()
			result = output[0].split("\n")[0]
			print 'result is %s' % result
			#TODO: make sure these work on all servers?
			notneeded = re.match("Already up-to-date.", result)
			needed = re.match("Updating .*", result)
		except:
			print 'error getting git update'
			return
		
		if notneeded:
			print 'update not needed'
			self.NEEDRELOAD = False
			return

		if needed:
			print 'update needed'
			self.NEEDRELOAD = True
			self.pluginreload(**kwargs)
			return

	def pluginreload(self, **kwargs):
		print 'pluginreload called'
		#Wait a couple minutes to allow clients to connect
		time.sleep(120)
		#Figure out how many clients are present
		kwargs['Broadcast'].broadcast("serverstatus")
	
	def onServerStatusResponse(self, *args, **kwargs):

		if self.NEEDRELOAD:
			gamemap = args[0]
			active = int(args[2])
			
			if active == 0:
				self.reload_plugins()
				kwargs['Broadcast'].broadcast("NextPhase; PrevPhase")
				self.NEEDRELOAD = False

	def logCommand(self, client, message, **kwargs):
		localtime = time.localtime(time.time())
		date = ("%s-%s-%s, %s:%s:%s" % (localtime[1], localtime[2], localtime[0], localtime[3], localtime[4], localtime[5]))
		f = open('admin.log', 'a')		
		f.write("Timestamp: \"%s\", Admin: %s, Command: %s\n" % (date, client, message))
		f.close

	def onTeamChange (self, *args, **kwargs):
		
		team = int(args[1])
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client['team'] = team

	#def onShuffle (self, clinum, **kwargs):
	def onShuffle (self, **kwargs):
		time.sleep(1)
		shufflelist = []

		#Put all the active players in a list
		for each in self.playerlist:
			if not each['active']:
				continue
			if each['team'] > 0:
				shufflelist.append(each)
	
		#sort shufflelists based on SF
		shufflelist = sorted(shufflelist, key=itemgetter('sf', 'level', 'clinum'), reverse=True)
		
		#randomly choose if we begin with human or beast
		r = random.randint(1,2)
		
		#Assign new teams, just like the K2 way, but Ino won't always be on humans
		for each in shufflelist:
		#TODO: is there a cleaner, more pythonic way to do this?	
			each['team'] = r
			if r == 1:
				r += 1
			elif r == 2:
				r -=1
			
		#Now actually do the shuffling
		for each in shufflelist:
			kwargs['Broadcast'].broadcast(\
				"SetTeam #GetIndexFromClientNum(%s)# %s"\
				 % (each['clinum'], each['team']))
		#Finish it off by going forward a phase
		kwargs['Broadcast'].broadcast(\
			"nextphase")
		#removed temporarily
		
		#kwargs['Broadcast'].broadcast(\
		#	"SendMessage %s You have shuffled the game." % (clinum))
		#Run balancer to get it nice and even
		#self.onBalance(clinum, **kwargs)
		self.onBalance(**kwargs)
		
	#def onBalance(self, clinum, **kwargs):
	def onBalance(self, **kwargs):
		time.sleep(1)
		teamone = []
		teamtwo = []

		#populate current team lists:
		for each in self.playerlist:
			if not each['active']:
				continue
			if each['team'] == 1:
				teamone.append(each)
			if each['team'] == 2:
				teamtwo.append(each)

		#Get Information about the teams
		
		teamonestats = self.getTeamInfo(teamone)
		teamtwostats = self.getTeamInfo(teamtwo)
		startstack = self.evaluateBalance(teamone, teamtwo)
		
		#Send message to admin that called the shuffle/balance
		#kwargs['Broadcast'].broadcast(\
		#	"SendMessage %s ^yPrior to balance: Team One Avg. SF was ^r%s^y median was ^r%s^y, Team Two Avg. SF was ^r%s^y median was ^r%s" \
		#	 % (clinum, teamonestats['avg'], teamonestats['median'], teamtwostats['avg'], teamtwostats['median']))

				
		#Find the players to swap
		lowest = -1
		pick1 = None
		pick2 = None
		
		for player1 in teamone:
			if player1['commander']:
				continue
			for player2 in teamtwo:
				if player2['commander']:
					continue
				#sort of inefficient to send the teamlist each time				
				ltarget = self.evaluateBalance(teamone, teamtwo, player1, player2, True)
				
				if (lowest < 0):
					lowest = ltarget
					pick1 = player1
					pick2 = player2
					continue
			
				if (lowest < ltarget):
					continue
			
				lowest = ltarget
				pick1 = player1
				pick2 = player2

		#If the stack isn't improved, abort it
		if (lowest >= startstack):
			print 'unproductive balance. terminate'
			kwargs['Broadcast'].broadcast(\
				"echo unproductive balance")
			return
		#Do the switch
		kwargs['Broadcast'].broadcast(\
			"set _index #GetIndexFromClientNum(%s)#;\
			 SetTeam #_index# 2;\
			 set _index #GetIndexFromClientNum(%s)#;\
			 SetTeam #_index# 1"\
			 % (pick1['clinum'], pick2['clinum']))

		teamonestats = self.getTeamInfo(teamone)
		teamtwostats = self.getTeamInfo(teamtwo)

		#kwargs['Broadcast'].broadcast(\
		#	"SendMessage %s ^yAfter balance: Team One Avg. SF was ^r%s^y median was ^r%s^y, Team Two Avg. SF was ^r%s^y median was ^r%s"\
		#	 % (clinum, teamonestats['avg'], teamonestats['median'], teamtwostats['avg'], teamtwostats['median']))


	def getTeamInfo(self, teamlist, **kwargs):
		
		teamsf = []
		combteamsf = float(0)		
		#figure out current averages and set some commonly used variables:
		for each in teamlist:
			combteamsf += each['sf']
			teamsf.append(each['sf'])
	
		sizeteam = len(teamlist)
		avgteam = combteamsf/sizeteam
		med = median(teamsf)
		
		teaminfo = {'size' : sizeteam, 'avg' : avgteam, 'total' : combteamsf, 'median' : med}
		
		return teaminfo

	def evaluateBalance(self, team1, team2, pick1=None, pick2=None, swap=False, **kwargs):
		#This function will swap out the picked players in a temporary list if swap is true and report the stack percent
		#If swap is false, it will just report the balance		
		#First, make new lists that we can modify:
		teamone = list(team1)
		teamtwo = list(team2)
		
		if swap:
			#Remove those players from the lists...		
			for each in teamone:
				if each['clinum'] == pick1['clinum']:
					teamone.remove(each) 
			for each in teamtwo:
				if each['clinum'] == pick2['clinum']:
					teamtwo.remove(each) 
		
			#Add to the lists		
			teamone.append(pick2)
			teamtwo.append(pick1)

		#Get the new team stats...
		teamonestats = self.getTeamInfo(teamone)
		teamtwostats = self.getTeamInfo(teamtwo)
		
		#Evaluate team balance
		teamoneshare = teamonestats['total']/(teamonestats['total'] + teamtwostats['total'])
		diffmedone = teamonestats['median']/(teamonestats['median'] + teamtwostats['median'])
		stack = teamoneshare + diffmedone
		return abs(stack - 1) * 100

	def onCommResign(self, *args, **kwargs):
		name = args[0]
		
		client = self.getPlayerByName(name)
		client['commander'] = False
		
	
	def onUnitChange(self, *args, **kwargs):
		if args[1] != "Player_Commander":
			return

		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client['commander'] = True

	def listClients(self, *args, **kwargs):

		kwargs['Broadcast'].broadcast("listclients")

	def onListClients(self, *args, **kwargs):
		clinum = args[0]
		name = args[2]
		client = self.getPlayerByName(name)
		client['active'] = True
		kwargs['Broadcast'].broadcast(\
		"echo CLIENT %s is on TEAM #GetTeam(|#GetIndexFromClientNum(%s)|#)#"\
		 % (client['clinum'], client['clinum']))

	def onRefreshTeams(self, *args, **kwargs):
		clinum = args[0]
		team = int(args[1])
		client = self.getPlayerByClientNum(clinum)
		client['team'] = team

