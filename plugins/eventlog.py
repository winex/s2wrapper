# -*- coding: utf-8 -*-

import os
import re
import time
import threading
import ConfigParser
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler
from operator import itemgetter
#This plugin was written by Old55 and he takes full responsibility for the junk below.
#He does not know python so the goal was to make something functional, not something
#efficient or pretty.


class eventlog(ConsolePlugin):
	VERSION = "0.0.1"
	ms = None
	PHASE = 0
	STARTSTAMP = 0
	playerlist = []
	eventlist = []
	eventbuffer = []
	objectlist = []
	typelist = []
	TIME = 0
	GAMETIME = 0
	EVENT = 0
	MATCH = 0
	SERVER = 0
	MAP = None
	base = None
	sent = None

	def onPluginLoad(self, config, **kwargs):
		#TODO: read stats directory from sendstats.ini, put that before .event file that gets written
		ini = ConfigParser.ConfigParser()
		ini.read(config)

		stats = os.path.join(os.path.dirname(config),'sendstats.ini')	
		ini.read(stats)
		
		for (name, value) in ini.items('paths'):
			if (name == "base"):
				self.base = value
			if (name == "sent"):
				self.sent = value

	
		self.objectlist = [
('Building_Academy','Academy'),\
('Building_Armory','Armory'),\
('Building_ArrowTower','Arrow Tower'),\
('Building_CannonTower','Cannon Tower'),\
('Building_CharmShrine','Charm Shrine'),\
('Building_ChlorophilicSpire','Chlorophilic Spire'),\
('Building_EntangleSpire','Static Spire'),\
('Building_Garrison','Garrison'),\
('Building_GroveMine','Grove Mine'),\
('Building_HumanHellShrine','Hell Shrine'),\
('Building_Lair','Lair'),\
('Building_Monastery','Monastery'),\
('Building_Nexus','Nexus'),\
('Building_PredatorDen','Predator Den'),\
('Building_Sanctuary','Sanctuary'),\
('Building_ShieldTower','Shield Tower'),\
('Building_SiegeWorkshop','Siege Workshop'),\
('Building_SteamMine','Steam Mine'),\
('Building_StrataSpire','Strata Spire'),\
('Building_Stronghold','Stronghold'),\
('Building_SubLair','Sublair'),\
('Team1','Humans'),\
('Team2','Beasts'),\
('Gadget_AmmoDepot','Ammo Depot'),\
('Gadget_BeastSpawnPortal','Spawn Portal'),\
('Gadget_DemoCharge','Demo Charge'),\
('Gadget_ElectricEye','Electric Eye'),\
('Gadget_HumanOfficerSpawnFlag','Spawn Portal'),\
('Gadget_ManaFountain','Mana Fountain'),\
('Gadget_Sentry','Sentry Bat'),\
('Gadget_ShieldGenerator','Shield Generator'),\
('Gadget_SteamTurret','Steam Turret'),\
('Gadget_Venus','Poison Venus'),\
('Player_BatteringRam','Battering Ram'),\
('Player_Behemoth','Behemoth'),\
('Player_Chaplain','Chaplain'),\
('Player_Commander','Commander'),\
('Player_Conjurer','Conjurer'),\
('Player_Devourer','Devourer'),\
('Player_Engineer','Builder'),\
('Player_Hunter','Hunter'),\
('Player_Legionnaire','Legionnaire',),\
('Player_Maliken','Maliken'),\
('Player_Malphas','Malphas'),\
('Player_Marksman','Marksman'),\
('Player_Observer','Spectator'),\
('Player_Predator','Predator'),\
('Player_Revenant','Revenant'),\
('Player_Savage','Savage'),\
('Player_Shaman','Shaman',),\
('Player_ShapeShifter','Shape Shifter'),\
('Player_Steambuchet','Steambuchet'),\
('Player_Summoner','Summoner'),\
('Player_Tempest','Tempest'),\
('None','None')]		
		pass
	
	def onPhaseChange(self, *args, **kwargs):

		phase = int(args[0])
		self.PHASE = phase

		if phase == 6:
			#built
			kwargs['Broadcast'].broadcast(\
			"RegisterGlobalScript -1 \"RegisterEntityScript #GetScriptParam(index)# death \\\"Set _objdead #GetScriptParam(index)#;\
			 									          Set _killer #GetScriptParam(attackingindex)#;\
													  ExecScript ObjectDeath\\\";\
			echo EVENT built #GetScriptParam(type)# on None by None of type None at #GetScriptParam(posx)# #GetScriptParam(posy)# 0.0; echo\" buildingplaced")
			
			#placed gadget
			kwargs['Broadcast'].broadcast(\
			"RegisterGlobalScript -1 \"RegisterEntityScript #GetScriptParam(gadgetindex)# death \\\"Set _objdead #GetScriptParam(index)#;\
			 									                Set _killer #GetScriptParam(attackingindex)#;\
													        ExecScript ObjectDeath\\\";\
			echo EVENT placed #GetScriptParam(type)# on -1 by #GetClientNumFromIndex(|#GetScriptParam(index)|#)# of type #GetType(|#GetScriptParam(index)|#)# at #GetScriptParam(posx)# #GetScriptParam(posy)# 0.0; echo\" placegadget")

			#spawn
			kwargs['Broadcast'].broadcast(\
			"RegisterGlobalScript -1 \"RegisterEntityScript #GetScriptParam(index)# death \\\"Set _dead #GetScriptParam(index)#;\
			 									          Set _killer #GetScriptParam(attackingindex)#;\
													  ExecScript PlayerDeath\\\";\
			 set _spindex #GetScriptParam(index)#;\
			 set _spx #GetPosX(|#_spindex|#)#;\
			 set _spy #GetPosY(|#_spindex|#)#;\
			 echo EVENT spawn #GetType(|#GetScriptParam(index)|#)# on -1 by #GetClientNumFromIndex(|#GetScriptParam(index)|#)# of type None at #_spx# #_spy# 0.0; echo\" spawn")

			#changeteam, only for team 1 or 2
			kwargs['Broadcast'].broadcast(\
			"RegisterGlobalScript -1 \"set _team #GetScriptParam(newteam)#;\
						   if [_team > 0]\
						    echo EVENT join Team#_team# on -1 by #GetClientNumFromIndex(|#GetScriptParam(index)|#)# of type None at 0.0 0.0 0.0; echo\" changeteam")
			
			#playerleave
			kwargs['Broadcast'].broadcast(\
			"RegisterGlobalScript -1 \"set _team #GetTeam(|#GetScriptParam(index)|#)#;\
						   if [_team > 0]\
						    echo EVENT leave Team#_team# on -1 by ##GetScriptParam(clientid)# of type None at 0.0 0.0 0.0; echo\" playerleave")

				
			#ObjectDeath
			kwargs['Broadcast'].broadcast(\
			"RegisterGlobalScript -1 \"set _dx #GetPosX(|#_objdead|#)#;\
			 set _dy #GetPosY(|#_objdead|#)#;\
			 set _dz #GetPosZ(|#_objdead|#)#;\
			 echo EVENT killed #GetType(|#_objdead|#)# on -1 by #GetClientNumFromIndex(|#_killer|#)# of type #GetType(|#_killer|#)# at #_dx# #_dy# 0.0; echo\" ObjectDeath")
			
			#PlayerDeath
			kwargs['Broadcast'].broadcast(\
			"RegisterGlobalScript -1 \"set _dx #GetPosX(|#_dead|#)#;\
			 set _dy #GetPosY(|#_dead|#)#;\
			 set _dz #GetPosZ(|#_dead|#)#;\
			 set _nonplayer 0;\
			 set _ktype #GetType(|#_killer|#)#;\
			 if #StringEquals(|#_ktype|#,Npc_Critter)# set _nonplayer 1;\
			 if #StringEquals(|#_ktype|#,Building_ArrowTower)# set _nonplayer 1;\
			 if #StringEquals(|#_ktype|#,Building_CannonTower)# set _nonplayer 1;\
			 if #StringEquals(|#_ktype|#,Building_StrataSpire)# set _nonplayer 1;\
			 if #StringEquals(|#_ktype|#,Building_EntangleSpire)# set _nonplayer 1;\
			 if [_nonplayer == 0] echo EVENT killed #GetType(|#_dead|#)# on #GetClientNumFromIndex(|#_dead|#)# by #GetClientNumFromIndex(|#_killer|#)# of type #_ktype# at #_dx# #_dy# 0.0;\
			 if [_nonplayer == 1] echo EVENT killed #GetType(|#_dead|#)# on #GetClientNumFromIndex(|#_dead|#)# by None of type #_ktype# at #_dx# #_dy# 0.0; echo\" PlayerDeath")

			
		if phase == 7:

			self.eventlist.append({'map' : self.MAP, 'match' : self.MATCH, 'event' : -1})
			self.eventlist = sorted(self.eventlist, key=itemgetter('event'), reverse=False)
			self.endGame(**kwargs)
			self.STARTSTAMP = 0

		if phase == 5:
			self.GAMETIME = 0
			self.EVENT = 0
			self.STARTSTAMP = args[1]


	def getEvent(self, *args, **kwargs):

		if self.PHASE != 5:
			return

		self.EVENT += 1
		event = args[0]
		indexontype = args[1]
		on = args[2]
		by = args[3]
		indexbytype = args[4]
		x = (args[5])
		y = (args[6])
		z = (args[7])
		tm = self.EVENT
		location = ('%s %s %s' % (x, y, z))
		ontype = self.getObjectType(indexontype)
		bytype = self.getObjectType(indexbytype)
		clienton = self.getPlayerByClientNum(on)
		clientby = self.getPlayerByClientNum(by)

		eventbuffer =  ({'action' : event,\
				 'on_type' : ontype,\
				 'by_type' : bytype,\
				 'by' : clientby['name'],\
				 'byid' : clientby['acctid'],\
				 'on': clienton['name'],\
				 'onid': clienton['acctid'],\
				 'time' : self.GAMETIME,\
				 'coord' : location,\
				 'event' : tm})	
		
		self.eventlist.append(eventbuffer)


	def getMatchID(self, *args, **kwargs):

		self.MATCH = args[0]
		self.SERVER = args[1]
		print self.MATCH

	def getObjectType(self, indextype):
		
		for each in self.objectlist:
			if indextype == each[0]:
				return each[1]


	def getPlayerByClientNum(self, cli):
		
		for client in self.playerlist:
			if (client['clinum'] == cli):
				return client
		client = {'name' : 'None', 'acctid' : 'None'}
		return client


	def getPlayerByName(self, name):
		
		for client in self.playerlist:
			if (client['name'].lower() == name.lower()):
				return client

		client = {'name' : 'None', 'acctid' : 'None'}
		return client


	def onConnect(self, *args, **kwargs):
		
		id = args[0]
		ip = args[2]
		
		for client in self.playerlist:
			if (client['clinum'] == id):
				return
		
		self.playerlist.append ({'clinum' : id,\
					 'name' : 'X',\
					 'acctid' : 0,\
					 'active' : True
					 })

	def onAccountId(self, *args, **kwargs):

		cli = args[0]
		id = args[1]
				
		client = self.getPlayerByClientNum(cli)

		client['acctid'] = int(id)
		
	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client ['active'] = False
	

	def onSetName(self, *args, **kwargs):

		cli = args[0]
		playername = args[1]
		client = self.getPlayerByClientNum(cli)
		client ['name'] = playername
		
	def onServerStatus(self, *args, **kwargs):
		CURRENTSTAMP = int(args[1])
		self.MAP = args[0]
		self.TIME = int(CURRENTSTAMP) - int(self.STARTSTAMP)
		self.GAMETIME += 1
		
	def endGame(self, **kwargs):
		home  = os.environ['HOME']
		fname = ("%s.event" % (self.MATCH))
		full = os.path.join(home, self.base, fname)
		f = open(full, 'w')
		for each in self.eventlist:
			f.write("%s" % (each))
		f.close()
		
		self.eventlist = []


