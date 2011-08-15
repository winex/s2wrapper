# -*- coding: utf-8 -*-
# 7/27/11 - Massive changes to following. Number of followers is still in variable FOLLOWERS
import re
import math
import time
import ConfigParser
import threading
import os
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler

#This plugin was written by Old55 and he takes full responsibility for the junk below.
#He does not know python so the goal was to make something functional, not something
#efficient or pretty.

#NORMAL VERSION


class extras(ConsolePlugin):
	VERSION = "1.2.0"
	ms = None
	CHAT_INTERVAL = 10
	CHAT_STAMP = 0
	playerlist = []
	itemlist = []
	followlist = []
	FOLLOWERS = 4
	MAPSIZE = 0
	MAPSIZESET = False
	buildingprotect = False

	def onPluginLoad(self, config):
		self.ms = MasterServer ()
		
		ini = ConfigParser.ConfigParser()
		ini.read(config)
		
		pass
	
	def RegisterScripts(self, **kwargs):
		
		kwargs['Broadcast'].broadcast("RegisterGlobalScript -1 \"echo SCRIPT Client #GetScriptParam(clientid)# #GetScriptParam(what)# with value #GetScriptParam(value)#; echo\" scriptinput")
		#Setup everything for following
		self.followlist = []
		followers = 1
		framestring = ""
		
		while followers <= self.FOLLOWERS:
			followstring = ("\
					RegisterGlobalScript -1 \"set _follower{0} #GetIndexFromClientNum(|#_f{0}|#)#;\
					set _followed{0} #GetIndexFromClientNum(|#_fd{0}|#)#;\
					set _fx{0} #GetPosX(|#_followed{0}|#)#;\
					set _fy{0} #GetPosY(|#_followed{0}|#)#;\
					set _x{0} #GetPosX(|#_follower{0}|#)#;\
					set _y{0} #GetPosY(|#_follower{0}|#)#;\
					set _z{0} #GetPosZ(|#_follower{0}|#)#;\
					set _zs{0} #_x{0}#, #_y{0}#;\
					set _zt{0} #GetTerrainHeight(|#_zs{0}|#)#;\
					if [_z{0} < _zt{0}] set _z{0} [_zt{0} + 50];\
					set _followX{0} 200;\
					set _followY{0} 200;\
					SetPosition #_follower{0}# [_fx{0} + _followX{0}] [_fy{0} + _followY{0}] [_z{0}]\" follow{0}").format(followers)
			                    
			framestring += (";if [_f{0} >= 0] ExecScript follow{0}").format(followers)
			kwargs['Broadcast'].broadcast("%s" % (followstring))
			f = "_f{0}".format(followers)
			fd = "_fd{0}".format(followers)
			kwargs['Broadcast'].broadcast("set %s -1; set %s -1" % (f, fd))
			self.followlist.append({'follower' : -1, 'followed' : -1, 'f' : f, 'fd' : fd})
			followers += 1
			
		kwargs['Broadcast'].broadcast("RegisterGlobalScript -1 \"set _ii 0%s\" frame" % (framestring))

		

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
		
		if phase == 6:
			
			#remove stuck for players
			for each in self.playerlist:
				each['stuck'] = False
			#set buildig protect scripts

			#TODO: make sure the place it moves them is a valid position
			if self.buildingprotect:
				kwargs['Broadcast'].broadcast("\
				RegisterGlobalScript -1 \"RegisterEntityScript #GetScriptParam(index)# death \\\"Set _dead\
					#GetScriptParam(index)#; ExecScript Death\\\";\
				set _index #GetScriptParam(index)#; set _mz 350;\
				set _type #GetScriptParam(type)#; echo #_type#; if #StringEquals(|#_type|#,Building_HumanHellShrine)#\
				set _mz 2000; if #StringEquals(|#_type|#,Building_ArrowTower)# set _mz 2000;\
				if #StringEquals(|#_type|#,Building_CannonTower)# set _mz 2000;\
				if #StringEquals(|#_type|#,Building_ChlorophilicSpire)# set _mz 2000;\
				if #StringEquals(|#_type|#,Building_EntangleSpire)# set _mz 2000;\
				if #StringEquals(|#_type|#,Building_ShieldTower)# set _mz 2000;\
				if #StringEquals(|#_type|#,Building_StrataSpire)# set _mz 2000;\
				set _x #GetPosX(|#_index|#)#;\
				set _y #GetPosY(|#_index|#)#;\
				set _z #GetPosZ(|#_index|#)#;\
				SpawnEntityatEntity #_index# Trigger_Proximity model /core/null/null.mdf name DeathTrigger#_index# triggeronplayer 1 triggerradius\
					 250 triggerenter\
					 \\\"set _domove 1; set _xindex #GetScriptParam(index)#;\
					 set _xtype #GetType(|#_xindex|#)#;\
					 if #StringEquals(|#_xtype|#,Player_Behemoth)# set _domove 0;\
					 if #StringEquals(|#_xtype|#,Player_Malphas)# set _domove 0;\
					 if #StringEquals(|#_xtype|#,Player_Devourer)# set _domove 0;\
					 set _xx #GetPosX(|#_xindex|#)#;\
					 set _xy #GetPosY(|#_xindex|#)#;\
					 set _xz #GetPosZ(|#_xindex|#)#;\
					 if [_domove == 1] SetPosition #_xindex# [_xx + 300] [_xy - 300] #_xz#\\\";\
				 SetPosition #GetIndexFromName(DeathTrigger|#_index|#)# #_x# #_y# [_z + _mz];\
				 echo\" buildingplaced")

				kwargs['Broadcast'].broadcast("RegisterGlobalScript -1 \"RemoveEntity #GetIndexFromName(DeathTrigger|#_dead|#)#; echo\" Death");
				#get the map size
			mapthread = threading.Thread(target=self.getMapSize, args=(), kwargs=kwargs)
			mapthread.start()
				
		if phase == 7:
			for each in self.playerlist:
				each['team'] = 0
			self.MAPSIZESET = False

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
				each['follower'] = -1
				each['followed'] = -1
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

		for each in self.followlist:
			if each ['follower'] == client['clinum'] or each['followed'] == client['clinum']:
				each['follower'] = -1
				each['followed'] = -1
				self.follow(**kwargs)
				
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
	
	def onScriptEvent(self, *args, **kwargs):		
		
		caller = args[0]
		client = self.getPlayerByClientNum(caller)
		event = args[1]
		value = args[2]
				
		if event == 'Follow':
		#Determine if it is follow or stop
			if value == 'stop':
				action = value
				self.followaction(action, client, followed_player=None, **kwargs)
				return
			else:
				action = 'start'
				followed_player = self.getPlayerByName(value)
				if (followed_player ['team'] > 0) and (client ['team'] == 0):
					self.followaction(action, client, followed_player, **kwargs)
					return

		if event == 'SetMapPosition':
			
			if client['team'] != 0:
				return
			
			maxcoord = ((self.MAPSIZE - 1) * 64 * 64)
			print maxcoord
			location = re.match("(0\.\d+)_(0.\d+)", value)
			print location.group(1), location.group(2)
			coordx = float(location.group(1))*maxcoord
			coordy = float(location.group(2))*maxcoord
			print coordx, coordy
			kwargs['Broadcast'].broadcast(\
				 "SetPosition #GetIndexFromClientNum(%s)# %s %s #GetPosZ(|#GetIndexFromClientNum(%s)|#)#" % (client['clinum'], coordx, coordy, client['clinum']))
	def followaction(self, action, client, followed_player, **kwargs):
		
		if action == 'start':
		
			for each in self.followlist:
				#first check if they are already a follower
				if each ['follower'] == client['clinum']:
					each ['followed'] = followed_player['clinum']
					self.follow(**kwargs)
					return
				
			for each in self.followlist:
				#if not already follower, grab the first available spot
				if each['follower'] == -1:
					each ['follower'] = client['clinum']
					each ['followed'] = followed_player['clinum']
					self.follow(**kwargs)
					return
			#If all the spots are filled, report it
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^cThe follow list is full!" % (client['clinum']))
			return
						
		if action == 'stop':
			for each in self.followlist:
				if each['follower'] == client['clinum']:
					each['follower'] = -1
					each['followed'] = -1
		
		self.follow(**kwargs)
		
	def follow(self, **kwargs):
		for each in self.followlist:
			kwargs['Broadcast'].broadcast(\
			"set %s %s; set %s %s" % (each['f'], each['follower'], each['fd'], each['followed']))

	def getMapSize(self,**kwargs):
		
		checkdimension = 131071
		self.MAPSIZE = 10
		while not self.MAPSIZESET:
			time.sleep(0.5)
			self.MAPSIZESET = True
			checkdimension = checkdimension/2
			kwargs['Broadcast'].broadcast("echo #GetTerrainHeight(%s,0)#" % (checkdimension))
			print 'Map Size =', self.MAPSIZE
			time.sleep(1)

	def mapDimensions(self, *args, **kwargs):
		if self.MAPSIZE > 0:
			print 'made it to MAP DIMENSONS'
			self.MAPSIZE -= 1
			self.MAPSIZESET = False

