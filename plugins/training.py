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
		phase = int(args[0][0])
		print ('Current phase: %d' % (phase))
		if (phase == 5):
			self.onGameStart(*args, **kwargs)
			
	
	def onGameStart(self, *args, **kwargs):

		self.RegisterScripts(**kwargs)

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
		
		id = args[0][0]
		
		for client in self.playerlist:
			if (client['clinum'] == id):
				print 'already have entry with that clientnum!'
				return
		self.playerlist.append ({'clinum' : id, 'acctid' : 0, 'level' : 0, 'sf' : 0, 'lf' : 0, 'name' : 'X', 'team' : 0, 'oldteam' : 0, 'trainee' : -1})
		

	def onSetName(self, *args, **kwargs):

		print args
		
		cli = args[0][0]
		playername = args[0][1]
		

		client = self.getPlayerByClientNum(cli)

		client ['name'] = playername
		


	def onReceivedAccountId(self, *args, **kwargs):

	

		cli = args[0][0]
		id = args[0][1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		
		level = int(stats['level'])
		sf = int(stats['sf'])
		
		client = self.getPlayerByClientNum(cli)

		client ['acctid'] = int(id)
		client ['level'] = level
		client ['sf'] = sf
		
	def onTeamChange (self, *args, **kwargs):
		team = int(args[0][1])
		cli = args[0][0]
		client = self.getPlayerByClientNum(cli)
		client['team'] = team	
		print self.playerlist

	def onTrain (self, *args, **kwargs):
		name = args[0][1]
		trainer = self.getPlayerByName(args[0][1])
		trainee = args[0][2]
		
		
		for player in self.playerlist:
			if (player['name'] == trainee):
				toteam = player['team']	
				trainer['oldteam'] = trainer['team']
				trainer['team'] = toteam
				trainer['trainee'] = player['clinum']
				kwargs['Broadcast'].broadcast("set _value #GetIndexFromClientNum(%s)#; SetTeam #_value# %s; SendMessage %s You are now in a training session with %s" % (trainer['clinum'], toteam, trainer['clinum'], trainee))
					
	def onEndTrain (self, *args, **kwargs):
		name = args[0][1]
		trainer = self.getPlayerByName(args[0][1])
		if (trainer['trainee'] == -1):
			return
		kwargs['Broadcast'].broadcast("set _value #GetIndexFromClientNum(%s)#; SetTeam #_value# %s; SendMessage %s ^cYou have ended your training session.; SendMessage %s ^r%s ^chas ended their training session with you." % (trainer['clinum'], trainer['oldteam'], trainer['clinum'], trainer['trainee'], trainer['name']))
		trainer['team'] = trainer['oldteam']
		trainer['trainee'] == -1

