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
		kwargs['Broadcast'].put("RegisterGlobalScript -1 \"echo changing team....;MakeOfficer #GetScriptParam(clientid)#;  ChangeUnit #GetScriptParam(index)# Player_Savage true false false false false false false; ForceSpawn #GetScriptParam(changedindex)#;echo\" changeteam")
		kwargs['Broadcast'].put("set sv_squadsize 1")
		kwargs['Broadcast'].put("set _team 0")
		kwargs['Broadcast'].put("RegisterGlobalScript -1 \"CreateVar int _player_#GetScriptParam(clientid)#_duel -1;Set _maxteams #GetMaxTeams()#;Set _curclients #GetNumClients()#;if [_maxteams <= _curclients + 1] SetMaxTeams [_maxteams + 1];Set _maxteams #GetMaxTeams()#;Set _team [_team + 1];echo #_team#;Set _player_joining 1;SetTeam #GetScriptParam(index)# #_team#;MakeOfficer #GetScriptParam(clientid)#;ChangeUnit #GetScriptParam(index)# Player_Savage true false false false false false false;ForceSpawn #GetScriptParam(changedindex)#;Set _playerteam #GetTeam(|#GetScriptParam(changedindex)|#)#;Set _loop 1;Set _max #GetMaxTeams()#;ExecScript ally1;Set _player_joining 0;GiveExperience #GetScriptParam(index)# 1073741824;ResetAttributes #GetScriptParam(index)#;Set _message \\\"This is a duel arena that allows players to join the same team. By joining the same team you can use VOIP to communicate and help newer players. This also allows players to have team duels!\\\";Set _image /ui/commander/attack_down.tga;Set _header Welcome to the duel arena!;ClientExecScript #GetScriptParam(clientid)# Welcome header #_header# content #_message# texture #_image#;ClientExecScript #GetScriptParam(clientid)# SetupMusic; echo\" playerjoin")
		kwargs['Broadcast'].put("RegisterGlobalScript -1 \"if [_loop != _playerteam] AddAlliedTeam #_playerteam# #_loop#';if [_loop != _playerteam] AddAlliedTeam #_loop# #_playerteam#;Set _loop [_loop + 1];if [_loop < _max] ExecScript ally2; echo\" ally1")
		kwargs['Broadcast'].put("RegisterGlobalScript -1 \"if [_loop != _playerteam] AddAlliedTeam #_playerteam# #_loop#';if [_loop != _playerteam] AddAlliedTeam #_loop# #_playerteam#;Set _loop [_loop + 1];if [_loop < _max] ExecScript ally1; echo\" ally2")
		kwargs['Broadcast'].broadcast()
	
	def onServerStatus(self, *args, **kwargs):
		
		kwargs['Broadcast'].put("SendMessage -1 \"^cThis server allows training of players. Send the message: ^ytrain <playername> ^cto ^bALL^c chat to begin training. This will allow you to use in-game VOIP to communicate. End training by sending the message: ^yend training\"")
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
		self.playerlist.append({
			'clinum' : id,
			'acctid' : 0,
			'level'  : 0,
			'sf' : 0,
			'lf' : 0,
			'name' : 'X',
			'team' : 0,
			'oldteam' : 0,
			'trainee' : -1,
			'unit' : 'Player_Savage'
		})

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

		client['name'] = playername
		
	def onUnitChange(self, *args, **kwargs):
		cli = args[0]
		unit = args[1]

		client = self.getPlayerByClientNum(cli)
		if unit in self.unallowedlist:
			kwargs['Broadcast'].broadcast("set _value #GetIndexFromClientNum(%s)#; ChangeUnit #_value# %s true false false false false false false; SendMessage %s ^cYou can't select that unit. Sorry!" % (cli, client['unit'], cli))
			return
		client['unit'] = unit

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

		if (int(trainer['trainee']) > -1):
			kwargs['Broadcast'].broadcast("SendMessage %s You are currently in a training session. End that session first." % (trainer['clinum']))
			return

		if (player['name'].lower() == trainee.lower()):
			toteam = player['team']
			trainer['oldteam'] = trainer['team']
			trainer['team'] = toteam
			trainer['trainee'] = player['clinum']

			kwargs['Broadcast'].broadcast("set _value #GetIndexFromClientNum(%s)#; set X #GetPosX(|#_value|#)#; set Y #GetPosY(|#_value|#)#; set Z #GetPosZ(|#_value|#)#; echo CLIENT %s POSITION #X# #Y# #Z#" % (trainer['clinum'], trainer['clinum']))
			client = self.getPlayerByClientNum(trainer['clinum'])
			kwargs['Broadcast'].broadcast("set _value #GetIndexFromClientNum(%s)#; SetTeam #_value# %s; SendMessage %s You are now in a training session with %s; ChangeUnit #GetIndexFromClientNum(%s)# %s; SetPosition #_value# #X# #Y# #Z#" % (client['clinum'], toteam, client['clinum'], trainee, client['clinum'], client['unit']))

	def trainingEnd(self, name, **kwargs):
		trainer = self.getPlayerByName(name)
		if (int(trainer['trainee']) == -1):
			return
		kwargs['Broadcast'].broadcast("set _value #GetIndexFromClientNum(%s)#; SetTeam #_value# %s; SendMessage %s ^cYou have ended your training session.; SendMessage %s ^r%s ^chas ended their training session with you." % (trainer['clinum'], trainer['oldteam'], trainer['clinum'], trainer['trainee'], trainer['name']))
		trainer['team'] = trainer['oldteam']
		trainer['trainee'] = -1

