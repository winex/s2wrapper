# -*- coding: utf-8 -*-

import os
import re
import math
import time
import ConfigParser
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler

#This plugin was written by Old55 and he takes full responsibility for the junk below.
#He does not know python so the goal was to make something functional, not something
#efficient or pretty.


class training(ConsolePlugin):

	ms = None
	playerlist = []
	unallowedlist = []

	def onPluginLoad(self, config):
		self.ms = MasterServer ()

		ini = ConfigParser.ConfigParser()
		ini.read(config)
		#for (name, value) in config.items('balancer'):
		#	if (name == "level"):
		#		self._level = int(value)

		#	if (name == "sf"):
		#		self._sf = int(value)
		
		pass

	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		print ('Current phase: %d' % (phase))
		if (phase == 5):
			self.onGameStart(*args, **kwargs)
			
	
	def onGameStart(self, *args, **kwargs):

		self.RegisterScripts(**kwargs)
		self.unallowedunits(**kwargs)

	def RegisterScripts(self, **kwargs):
		#any extra scripts that need to go in can be done here
		#these are for identifying bought and sold items
		kwargs['Broadcast'].put("RegisterGlobalScript -1 \"echo changing team....; KillEntity #GetScriptParam(index)#; MakeOfficer #GetScriptParam(clientid)#;  ChangeUnit #GetScriptParam(index)# Player_Savage true false false false false false false; ForceSpawn #GetScriptParam(changedindex)#; echo\" changeteam")
		kwargs['Broadcast'].put("set sv_squadsize 1")
		kwargs['Broadcast'].broadcast()
	
	def onServerStatus(self, *args, **kwargs):
		
		kwargs['Broadcast'].put("SendMessage -1 ^cThis server allows training of players. Send the message: ^ytrain <playername> ^cto begin training. This will allow you to use in-game chat to communicate. End training by sending the message: ^yend training")
		kwargs['Broadcast'].broadcast()

	def getPlayerByClientNum(self, cli):

		for client in self.playerlist:
			if (client['clinum'] == cli):
				return client

	def getPlayerByName(self, name):

		for client in self.playerlist:
			if (client['name'] == name):
				return client

	def onConnect(self, *args, **kwargs):
		
		id = args[0]
		self.playerlist.append ({'clinum' : id, 'acctid' : 0, 'level' : 0, 'sf' : 0, 'lf' : 0, 'name' : 'X', 'team' : 0, 'oldteam' : 0, 'trainee' : -1})

	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		index = self.getPlayerIndex(cli)
		#index = self.playerlist.index(clinum[cli])
		print index
		del self.playerlist[index]
		print self.playerlist

	def getPlayerIndex (self, cli):
		
		indice = -1
		for player in self.playerlist:
			indice += 1
							
			if (player['clinum'] == cli):
				return indice	

	def onSetName(self, *args, **kwargs):

		print args
		
		cli = args[0]
		playername = args[1]

		client = self.getPlayerByClientNum(cli)

		client ['name'] = playername
		
	def onUnitChange(self, *args, **kwargs):
		cli = args[0]
		unit = args[1]

		for badunit in self.unallowedlist:
			if (badunit == unit):
				kwargs['Broadcast'].broadcast("set _value #GetIndexFromClientNum(%s)#; ChangeUnit #_value# Player_Savage true false false false false false false; SendMessage %s ^cYou can't select that unit. Sorry!" % (cli, cli))
				
	def unallowedunits(self, *args, **kwargs):

		self.unallowedlist = [
			'Player_Malphas',
			'Player_Maliken',
			'Player_Behemoth',
			'Player_Steambuchet',
			'Player_BatteringRam',
			'Player_Devourer',
			'Player_Tempest'
		]

	def onAccountId(self, *args, **kwargs):
		cli = args[0]
		id = args[1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		
		level = int(stats['level'])
		sf = int(stats['sf'])
		
		client = self.getPlayerByClientNum(cli)

		client ['acctid'] = int(id)
		client ['level'] = level
		client ['sf'] = sf
		
	def onTeamChange (self, *args, **kwargs):
		team = int(args[1])
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client['team'] = team	
		print self.playerlist

	def onMessage(self, *args, **kwargs):
		# process only ALL chat messages
		if args[0] != "ALL":
			return

		name = args[1]
		(func, arg) = args[2].split(None, 1)
		# only single person training is supported right now
		arg = arg.split(None, 1)

		if   func == "train" and arg:
			self.trainingStart(name, arg, **kwargs)
		elif func == "end" and arg == "training":
			return self.trainingEnd(name, **kwargs)

	def trainingStart(self, name, trainee, **kwargs):
		trainer = self.getPlayerByName(name)
		for player in self.playerlist:
			if (player['name'] == trainee):
				toteam = player['team']
				trainer['oldteam'] = trainer['team']
				trainer['team'] = toteam
				trainer['trainee'] = player['clinum']
				kwargs['Broadcast'].broadcast("set _value #GetIndexFromClientNum(%s)#; SetTeam #_value# %s; SendMessage %s You are now in a training session with %s" % (trainer['clinum'], toteam, trainer['clinum'], trainee))

	def trainingEnd(self, name, **kwargs):
		trainer = self.getPlayerByName(name)
		if (trainer['trainee'] == -1):
			return
		kwargs['Broadcast'].broadcast("set _value #GetIndexFromClientNum(%s)#; SetTeam #_value# %s; SendMessage %s ^cYou have ended your training session.; SendMessage %s ^r%s ^chas ended their training session with you." % (trainer['clinum'], trainer['oldteam'], trainer['clinum'], trainer['trainee'], trainer['name']))
		trainer['team'] = trainer['oldteam']
		trainer['trainee'] == -1

