# -*- coding: utf-8 -*-

import re
import math
import time
import ConfigParser
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler


class pug(ConsolePlugin):
	VERSION = "0.0.1"
	ms = None
	PHASE = 0
	STARTSTAMP = 0
	STARTED = False
	PICKING = False
	playerlist = []
	startinfo = {'h_captain' : None, 'h_ready' : False, 'h_first' : False, 'b_captain' : None, 'b_ready' : False, 'b_first' : False}
	TIME = 0
	
	def onPluginLoad(self, config):
		self.ms = MasterServer ()

		ini = ConfigParser.ConfigParser()
		ini.read(config)
		'''
		for (name, value) in ini.items('var'):
			if (name == "clan1"):
				self.CLAN1 = value
			if (name == "clan2"):
				self.CLAN2 = value
		'''
		pass


	def onStartServer(self, *args, **kwargs):
		
		self.PHASE = 0
		self.playerlist = []
		self.startinfo = {'h_captain' : None, 'h_ready' : False, 'h_first' : False, 'b_captain' : None, 'b_ready' : False, 'b_first' : False}

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
				return
		
		self.playerlist.append ({'clinum' : id,\
					 'acctid' : 0,\
					 'level' : 0,\
					 'ip' : ip,\
					 'sf' : 0,\
					 'name' : 'X',\
					 'active' : False,\
					 'team' : 0,\
					 'ping' : 0,\
					 'clan' : 'X'})

		kwargs['Broadcast'].broadcast("SendMessage %s ^cTo toggle your PUG availability send the chat message ^rpug noplay" % (id))
		
	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client ['active'] = False
	
		if client['clinum'] == self.startinfo['h_captain']:
			self.startinfo['h_captain'] = None
			self.startinfo['h_ready'] = False
			kwargs['Broadcast'].broadcast("set State_Interrupted_EffectPath \"trigger UpdateDetail 1\"")
		if client['clinum'] == self.startinfo['b_captain']:
			self.startinfo['b_captain'] = None
			self.startinfo['b_ready'] = False
			kwargs['Broadcast'].broadcast("set Gadget_Hail_ModelPath \"trigger UpdateError 1\"")
			
	def onSetName(self, *args, **kwargs):

		cli = args[0]
		playername = args[1]
		client = self.getPlayerByClientNum(cli)
		client ['name'] = playername					
		client ['play'] = True

	def onAccountId(self, *args, **kwargs):

		cli = args[0]
		id = args[1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		
		level = int(stats['level'])
		sf = int(stats['sf'])
		exp = int(stats['exp'])
		time = int(stats['secs'])
		time = time/60
		sf = int(exp/time)
		clan = stats['clan_tag']
		client = self.getPlayerByClientNum(cli)
		
		client ['acctid'] = int(id)
		client ['level'] = level
		client ['sf'] = sf
		client ['active'] = True
		client ['clan'] = clan
		client ['newteam'] = 0
		
		
	def onTeamChange (self, *args, **kwargs):

		team = int(args[1])
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client['team'] = team

	def onGameStart (self, *args, **kwargs):
		
		self.STARTSTAMP = args[1]

	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		self.PHASE = phase

		if phase == 5:
			self.STARTSTAMP = args[1]
			self.STARTED = True
		if phase == 6:
			self.PICKING = False
			self.STARTED = False
			self.startinfo = {'h_captain' : None, 'h_ready' : False, 'h_first' : False, 'b_captain' : None, 'b_ready' : False, 'b_first' : False}
			kwargs['Broadcast'].broadcast("set State_SuccessfulBlock_Description -1;\
							set State_Interrupted_EffectPath \"trigger UpdateDetail 1\";\
							set Gadget_Hail_ModelPath \"trigger UpdateError 1\";\
							set State_ImpPoisoned_Name \"trigger UpdateSpeed 1\";\
							set Gadget_Hail_Description \"trigger UpdatePercent -1\";\
							set State_ImpPoisoned_ExpiredEffectPath \"trigger UpdateExtraction 1\";\
							set maxteams 3;\
							set Pet_Shaman_Prerequisite 1;\
							set sv_setupTimeCommander 600000000;\
							Set sv_maxteamdifference 30;")
			kwargs['Broadcast'].broadcast("RegisterGlobalScript -1 \"echo SCRIPT Client #GetScriptParam(clientid)# #GetScriptParam(what)# with value #GetScriptParam(value)#; echo\" scriptinput")
		if phase == 7:
			for each in self.playerlist:
				each['newteam'] = 0
	
	def onMessage(self, *args, **kwargs):
		
		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
		
		noplay = re.match("pug noplay", message, flags=re.IGNORECASE)
		
		if noplay:
			self.togglePlay(client, **kwargs)
	
	def togglePlay(self, client, playing=None, **kwargs):
		color = '^g'
		if self.PICKING:
				kwargs['Broadcast'].broadcast("SendMessage %s ^rYou cannot toggle your status once picking has begun." % (client['clinum']))
				return
		if not playing:
			if client['play']:
				client['play'] = False
				color = '^r'
			else:
				client['play'] = True
		else:
			client['play'] = playing
			if not client['play']:
				color = '^r' 
		kwargs['Broadcast'].broadcast("SendMessage %s ^cYour Playing Status: %s%s" % (client['clinum'], color, client['play']))
	
	
	def onScriptEvent(self, *args, **kwargs):		
		
		caller = args[0]
		client = self.getPlayerByClientNum(caller)
		event = args[1]
		value = args[2]
		info = self.startinfo
		
		#Captain select
		if event == 'Captain':
			if caller == info['b_captain'] or caller == info['h_captain']:
				return
			if value == 'beasts':
				info['b_captain'] = caller
				kwargs['Broadcast'].broadcast("set Gadget_Hail_ModelPath \"trigger UpdateError 0\"; SendMessage -1 ^r%s^w is Captain of the Beasts!" % (client['name']))
				if not info['h_captain']:
					info['h_first'] = True
				else:
					self.beginpicking(**kwargs)
			if value == 'humans':
				info['h_captain'] = caller
				kwargs['Broadcast'].broadcast("set State_Interrupted_EffectPath \"trigger UpdateDetail 0\";  SendMessage -1 ^r%s^w is Captain of the Humans!" % (client['name']))
				if not info['b_captain']:
					info['b_first'] = True
				else:
		
					self.beginpicking(**kwargs)
			print info
			
		#Toggle player availability
		if event == 'Toggle':
			playing = False
			if value == 'true':
				playing = True

			self.togglePlay(client, playing, **kwargs)
			
		#Player select
		if event == 'Select':
			player = self.getPlayerByName(value)
			
			if caller == info['h_captain']:
				if not player['play']:
					kwargs['Broadcast'].broadcast("SendMessage %s ^rThat player has requested to not play in this match." % (client['clinum']))
					return
				player['newteam'] = 1
				client['newteam'] = 1
				kwargs['Broadcast'].broadcast("SendMessage -1 ^r%s^w has selected ^y%s ^wfor the Humans!" % (client['name'], player['name']))
				kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; SetTeam #_index# 1" % (player['clinum']))
				kwargs['Broadcast'].broadcast("set State_SuccessfulBlock_Description %s; set Gadget_Hail_Description \"trigger UpdatePercent %s\"" % (info['b_captain'], info['b_captain']))
				
			if caller == info['b_captain']:
				if not player['play']:
					kwargs['Broadcast'].broadcast("SendMessage %s ^rThat player has requested to not play in this match." % (client['name']))
					return
				player['newteam'] = 2
				client['newteam'] = 2
				kwargs['Broadcast'].broadcast("SendMessage -1 ^r%s^w has selected ^y%s ^wfor the Beasts!" % (client['name'], player['name']))
				kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; SetTeam #_index# 2" % (player['clinum']))
				kwargs['Broadcast'].broadcast("set State_SuccessfulBlock_Description %s; set Gadget_Hail_Description \"trigger UpdatePercent %s\"" % (info['h_captain'],info['h_captain'] ))
		#Ready
		if event == 'Ready':
			if self.STARTED:
				return
			if caller == info['h_captain']:
				info['h_ready'] = True
				kwargs['Broadcast'].broadcast("SendMessage -1 ^r%s^w has indicated that Humans are ready!" % (client['name']))
			if caller == info['b_captain']:
				info['b_ready'] = True
				kwargs['Broadcast'].broadcast("SendMessage -1 ^r%s^w has indicated that Beasts are ready!" % (client['name']))
			#Start the game if both captains say they are ready
			if info['h_ready'] and info['b_ready']:
				kwargs['Broadcast'].broadcast("set State_ImpPoisoned_Name \"trigger UpdateSpeed 0\"")
				self.populate(**kwargs)
				
	def beginpicking(self, **kwargs):
		self.PICKING = True
		#start by making the teams unjoinable: doesn't seem to work
		kwargs['Broadcast'].broadcast("set sv_maxteamdifference 1; set State_ImpPoisoned_ExpiredEffectPath \"trigger UpdateExtraction 0\";")
		#move everyone to spectator, but move captains to the appropriate team
		for each in self.playerlist:
			if each['active']:
				kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; SetTeam #_index# 0" % (each['clinum']))
			if each['clinum'] == self.startinfo['h_captain']:
				kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; SetTeam #_index# 1" % (each['clinum']))
			if each['clinum'] == self.startinfo['b_captain']:
				kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; SetTeam #_index# 2" % (each['clinum']))
		#Set variables to get the first captain to start picking
		if self.startinfo['h_first']:
			kwargs['Broadcast'].broadcast("set State_SuccessfulBlock_Description %s; set Gadget_Hail_Description \"trigger UpdatePercent %s\"" % (self.startinfo['h_captain'], self.startinfo['h_captain']))
		else:
			kwargs['Broadcast'].broadcast("set State_SuccessfulBlock_Description %s; set Gadget_Hail_Description \"trigger UpdatePercent %s\"" % (self.startinfo['b_captain'], self.startinfo['b_captain']))

	def populate(self, **kwargs):
	
		for each in self.playerlist:
			if each['active']:
				kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; SetTeam #_index# %s" % (each['clinum'], each['newteam']))
		#Send to the next phase
		kwargs['Broadcast'].broadcast("NextPhase; set sv_setupTimeCommander 60000; PrevPhase")
