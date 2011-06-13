# -*- coding: utf-8 -*-
# 3/19/11 - Modified BF calculation and balance calculation
import re
import math
import time
import ConfigParser
import threading
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler

#This plugin was written by Old55 and he takes full responsibility for the junk below.
#He does not know python so the goal was to make something functional, not something
#efficient or pretty.

#NORMAL VERSION


class extras(ConsolePlugin):
	VERSION = "1.0.9"
	ms = None
	CHAT_INTERVAL = 10
	CHAT_STAMP = 0
	playerlist = []
	itemlist = []
	followlist = []
	buildingprotect = False

	def onPluginLoad(self, config):
		self.ms = MasterServer ()
		
		ini = ConfigParser.ConfigParser()
		ini.read(config)
		
		pass
	
	def RegisterScripts(self, **kwargs):
		
		print 'register scripts'
		
	def getPlayerByClientNum(self, cli):

		client = None

		for client in self.playerlist:
			if (client['clinum'] == cli):
				return client

	def getPlayerByName(self, name):

		client = None

		for client in self.playerlist:
			if (client['name'].lower() == name.lower()):
				return client

	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		self.RegisterScripts(**kwargs)
		
		self.followlist = []
		self.follow(**kwargs)

		if phase == 6:
			for each in self.playerlist:
				each['stuck'] = False
			if self.buildingprotect:
				kwargs['Broadcast'].broadcast("RegisterGlobalScript -1 \"RegisterEntityScript #GetScriptParam(index)# death \\\"Set _dead #GetScriptParam(index)#; ExecScript Death\\\"; set _index #GetScriptParam(index)#; set _mz 350; set _type #GetScriptParam(type)#; echo #_type#; if #StringEquals(|#_type|#,Building_HumanHellShrine)# set _mz 2000; if #StringEquals(|#_type|#,Building_ArrowTower)# set _mz 2000; if #StringEquals(|#_type|#,Building_CannonTower)# set _mz 2000; if #StringEquals(|#_type|#,Building_ChlorophilicSpire)# set _mz 2000; if #StringEquals(|#_type|#,Building_EntangleSpire)# set _mz 2000; if #StringEquals(|#_type|#,Building_ShieldTower)# set _mz 2000; if #StringEquals(|#_type|#,Building_StrataSpire)# set _mz 2000; set _x #GetPosX(|#_index|#)#; set _y #GetPosY(|#_index|#)#; set _z #GetPosZ(|#_index|#)#; SpawnEntityatEntity #_index# Trigger_Proximity model /core/null/null.mdf name DeathTrigger#_index# triggeronplayer 1 triggerradius 250 triggerenter \\\"set _domove 1; set _xindex #GetScriptParam(index)#; set _xtype #GetType(|#_xindex|#)#; if #StringEquals(|#_xtype|#,Player_Behemoth)# set _domove 0; if #StringEquals(|#_xtype|#,Player_Malphas)# set _domove 0; if #StringEquals(|#_xtype|#,Player_Devourer)# set _domove 0; set _xx #GetPosX(|#_xindex|#)#; set _xy #GetPosY(|#_xindex|#)#; set _xz #GetPosZ(|#_xindex|#)#; if [_domove == 1] SetPosition #_xindex# [_xx + 300] [_xy - 300] #_xz#\\\"; SetPosition #GetIndexFromName(DeathTrigger|#_index|#)# #_x# #_y# [_z + _mz]; echo\" buildingplaced")
				kwargs['Broadcast'].broadcast("RegisterGlobalScript -1 \"RemoveEntity #GetIndexFromName(DeathTrigger|#_dead|#)#; echo\" Death");
	def onConnect(self, *args, **kwargs):
		
		id = args[0]
		
		for client in self.playerlist:
			if (client['clinum'] == id):
				return

		self.playerlist.append ({
		 'clinum' : id,\
		 'acctid' : 0,\
		 'level' : 0,\
		 'sf' : 0,\
		 'lf' : 0,\
		 'name' : 'X',\
		 'team' : 0,\
		 'stuck' : False,\
		 'index' : 0,\
		 'exp' : 2,\
		 'value' : 150,\
		 'prevent' : 0,\
		 'active' : False,\
		 'gamelevel' : 1})
	
	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client ['active'] = False
		
		for each in self.followlist:
			if each ['follower'] == client['clinum'] or each['followed'] == client['clinum']:
				self.followlist.remove(each)
				self.follow(**kwargs)
				
	def onSetName(self, *args, **kwargs):

				
		cli = args[0]
		playername = args[1]
		
		client = self.getPlayerByClientNum(cli)
		client ['name'] = playername
		mapmessage = "^cSpectators on this server can follow individual players. Send the message: ^rfollow playername. ^cTo stop following: ^rstop follow.\
			      ^cIf you get stuck on the map you can send the message: ^rstuck^c to nudge you out of your spot. This can be used once a game."
		kwargs['Broadcast'].broadcast("SendMessage %s %s" % (client['clinum'], mapmessage))
		
	def onAccountId(self, *args, **kwargs):

		cli = args[0]
		id = args[1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		
		level = int(stats['level'])
		sf = int(stats['sf'])
		lf = int(stats['lf'])
		exp = int(stats['exp'])
		time = int(stats['secs'])
		
		client = self.getPlayerByClientNum(cli)

		client ['acctid'] = int(id)
		client ['level'] = level
		client ['sf'] = sf
		client ['lf'] = lf
		client ['exp'] = exp
		client ['active'] = True

	def onTeamChange (self, *args, **kwargs):
		
		team = int(args[1])
		cli = args[0]
		
		client = self.getPlayerByClientNum(cli)
		client['team'] = team


	def onMessage(self, *args, **kwargs):
		
		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
		
		#Various chat matches
		followed = re.match("follow (\S+)", message, flags=re.IGNORECASE)
		stopfollow = re.match("stop follow", message, flags=re.IGNORECASE)
		stuck = re.match("stuck", message, flags=re.IGNORECASE)

		if followed:
			action = 'start'
			followed_player = self.getPlayerByName(followed.group(1))
			if followed_player == None:
				kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^cCould not find a player by that name." % (client['clinum']))
				return
			
			if (followed_player ['team'] > 0) and (client ['team'] == 0):
				self.followaction(action, client, followed_player, **kwargs)

		if stopfollow:
			action = 'stop'
			self.followaction(action, client, followed_player=None, **kwargs)
			
		if stuck:
			if client['stuck']:
				return
			kwargs['Broadcast'].broadcast(\
				"set _stuckindex #GetIndexFromClientNum(%s)#;\
				 set _X [rand*100]; echo #_X#;\
				 set _Y [rand*100]; echo #_Y#;\
				 set _stuckx #GetPosX(|#_stuckindex|#)#;\
				 set _stucky #GetPosY(|#_stuckindex|#)#;\
				 set _stuckz #GetPosZ(|#_stuckindex|#)#;\
				 SetPosition #_stuckindex# [_stuckx + _X] [_stucky + _Y] [_stuckz + 40]" % (client['clinum']))

			client['stuck'] = True
	
	def followaction(self, action, client, followed_player, **kwargs):
		
		if action == 'start':
			for each in self.followlist:
				if each ['follower'] == client['clinum']:
					each ['followed'] = followed_player['clinum']
					self.follow(**kwargs)
					return
				#append to player list			
			self.followlist.append ({'follower' : client['clinum'], 'followed' : followed_player['clinum']})
			
		if action == 'stop':
			for each in self.followlist:
				if each['follower'] == client['clinum']:
					self.followlist.remove(each)
		
		self.follow(**kwargs)
		
	def follow(self, **kwargs):
		
		followlist = []
		for each in self.followlist:
			followline =  (";set _follower%s #GetIndexFromClientNum(%s)#;\
					set _followed%s #GetIndexFromClientNum(%s)#;\
					set _fx #GetPosX(|#_followed%s|#)#;\
					set _fy #GetPosY(|#_followed%s|#)#;\
					set _z #GetPosZ(|#_follower%s|#)#;\
					set _followX 200;\
					set _followY 200;\
					SetPosition #_follower%s# [_fx + _followX] [_fy + _followY] [_z]"\
					 % (each['follower'],\
					    each['follower'],\
					    each['followed'],\
					    each['followed'],\
					    each['followed'],\
					    each['followed'],\
					    each['follower'],\
					    each['follower']))
		
			followlist.append(followline)	
	
			
		mainbody = ''.join(followlist)
		
		
		if mainbody == None:
			script = ("RegisterGlobalScript -1 \"set _xmod 1.0; set _ymod -1.0\" frame")
			kwargs['Broadcast'].broadcast("%s" % (script))
			return

		script = ("RegisterGlobalScript -1 \"set _xmod 1.0; set _ymod -1.0 %s\" frame" % (mainbody))
				
		kwargs['Broadcast'].broadcast("%s" % (script))
