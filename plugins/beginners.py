# -*- coding: utf-8 -*-
# 12/29/10 - Added kill count check after 5 minutes. If player has more than 3 times the Avg. number of kills, boot them. Turned off level check.
import re
import math
import time
import ConfigParser
import threading
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler


class beginners(ConsolePlugin):
	VERSION = "0.0.2"
	ms = None
	TIME = 0
	GAMESTARTED = 0
	STARTSTAMP = 0
	CHAT_INTERVAL = 10
	CHAT_STAMP = 0
	PHASE = 0
	MATCHES = 0
	playerlist = []
	
	def onPluginLoad(self, config):
		self.ms = MasterServer ()

		ini = ConfigParser.ConfigParser()
		ini.read(config)
		#for (name, value) in config.items('beginners'):
		#	if (name == "level"):
		#		self._level = int(value)

		#	if (name == "sf"):
		#		self._sf = int(value)
		
		pass

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
		for client in self.playerlist:
			if (client['clinum'] == id):
				print 'already have entry with that clientnum!'
				return

		self.playerlist.append ({'clinum' : id, 'acctid' : 0, 'level' : 0, 'sf' : 0, 'name' : 'X', 'active' : 0, 'banned' : False, 'ip' : ip, 'banstamp' : 0, 'kills' : 0})


	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client ['active'] = 0
	

	def onSetName(self, *args, **kwargs):

		cli = args[0]
		playername = args[1]
		client = self.getPlayerByClientNum(cli)
		client ['name'] = playername
		

	def onAccountId(self, *args, **kwargs):

		doKick = False
		reason1 = "This is a beginners server. Please go play on a normal server."
		reason2 = "You (or someone at your IP address) have been temporarily prohibited from this server."
		reason3 = "Please go play on normal server."
		cli = args[0]
		id = args[1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		
		level = int(stats['level'])
		sf = int(stats['sf'])
		wins = int(stats['wins'])
		losses = int(stats['losses'])
		dcs = int(stats['d_conns'])
		total = wins + losses + dcs

		client = self.getPlayerByClientNum(cli)

		client ['acctid'] = int(id)
		client ['level'] = level
		client ['sf'] = sf
		client ['active'] = 1

		if client['banned']:
			reason = reason3
			doKick = True		

		for each in self.playerlist:
			if each['banned'] and (each['ip'] == client['ip']):
				reason = reason2
				doKick = True
				

		if (sf > 160) and (total > 4):
			reason = reason1
			doKick = True
			client ['banned'] = True
			client ['banstamp'] = self.MATCHES
		
		if doKick:
			kwargs['Broadcast'].broadcast("kick %s \"%s\"" % (cli, reason))

		print client

	def onTeamChange (self, *args, **kwargs):
		
		team = int(args[1])
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		if (team > 0):
			client['active'] = 1
		if (team == 0):
			client['active'] = 0

	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		self.PHASE = phase
	
		if (phase == 7):
			self.onGameEnd()
		if (phase == 5):
			self.onGameStart(*args, **kwargs)
					
		
	def onGameEnd(self, *args, **kwargs):
		
		self.MATCHES += 1
		#all players are unbanned after 15 matches
		for each in self.playerlist:
			each['kills'] = 0
			each['active'] = 0
			duration = self.MATCHES - int(each['banstamp'])
			if duration > 9:
				each['banned'] = False

		self.GAMESTARTED = 0


	def onGameStart (self, *args, **kwargs):
		
		
		self.STARTSTAMP = args[1]
		self.GAMESTARTED = 1
		for each in self.playerlist:
			each['kills'] = 0
	
	def onServerStatus(self, *args, **kwargs):
		CURRENTSTAMP = int(args[1])
		self.TIME = int(CURRENTSTAMP) - int(self.STARTSTAMP)
			
		if self.PHASE == 5:
			if (self.TIME > (5 * 60 * 1000)):
				self.smurfCheck (**kwargs)	

	def onGetLevels(self, *args, **kwargs):
		clinum = args[0]
		level = int(args[1])
		client = self.getPlayerByClientNum(clinum)
		

	def retrieveLevels(self, cli, **kwargs):

		#kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; set _plevel #GetLevel(|#_index|#)#;echo CLIENT %s is LEVEL #_plevel#; set _plevel 1" % (cli, cli))
		kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; set _pteam #GetTeam(|#_index|#)#; set _plevel #GetLevel(|#_index|#)#; if [_pteam > 0] echo CLIENT %s is LEVEL #_plevel#; set _plevel 1; set _pteam 0" % (cli, cli))


	def getTeamLevels(self, **kwargs):
	
		for player in self.playerlist:
			if player['active'] == 1:
				self.retrieveLevels(player['clinum'], **kwargs)


	def onGetLevels(self, *args, **kwargs):
		clinum = args[0]
		level = int(args[1])
		client = self.getPlayerByClientNum(clinum)
		doKick = False
		reason = "This is either a smurf account or you are too good for this server. You should play on another server."
		if level > 6:
			doKick = True
			client ['banned'] = True
			client ['banstamp'] = self.MATCHES

		if doKick:
			kwargs['Broadcast'].broadcast("kick %s \"%s\"" % (cli, reason))	
		
	def onHasKilled(self, *args, **kwargs):
		print args
		killed = self.getPlayerByName(args[0])
		killer = self.getPlayerByName(args[1])
		
		killer['kills'] += 1
		print killer
		print killed
	def smurfCheck(self, **kwargs):
		
		totalkills = 0
		activeplayers = 0
		avgkills = 0
		reason = "Congratulations! You have done a great job and have graduated from this server."

		for each in self.playerlist:
			if each['active'] == 1:
				activeplayers += 1
				totalkills += int(each['kills'])

		avgkills = int(totalkills/activeplayers)

		for players in self.playerlist:
			if (players['kills'] > (avgkills * 3)):
				cli = players['clinum']
				players['banned'] = True
				players['banstamp'] = self.MATCHES
				kwargs['Broadcast'].broadcast("kick %s \"%s\"" % (cli, reason))
				
	def onMessage(self, *args, **kwargs):
		
		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
		
		if (args[0] == "SQUAD") and (message == 'report bans'):
			for bans in self.playerlist:
				if bans['banned']:
					kwargs['Broadcast'].broadcast("SendMessage %s Banned: %s, IP: %s" % (client['clinum'], bans['name'], bans['ip']))


