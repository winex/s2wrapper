# -*- coding: utf-8 -*-
# THIS PLUGIN REQUIRES A SPECIFIC MAP. It can be modified for other maps, but note that the blocker list needs to be changed
# 3.19.11 - Added admin control: kick, cancel
import re
import math
import time
import ConfigParser
import threading
from MasterServer import MasterServer
from StatsServers import StatsServers
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler
from operator import itemgetter

#This plugin was written by Old55 and he takes full responsibility for the junk below.
#He does not know python so the goal was to make something functional, not something
#efficient or pretty.

#NORMAL VERSION


class tournament(ConsolePlugin):
	VERSION = "1.0.2"
	STARTED = 0
	MINIMUM =  2
	RECRUIT = False
	ORGANIZER = -1
	DUELROUND = 0
	TOURNEYROUND = 0
	MISSING = -1
	DOUBLEELIM = False
	CANCEL = False
	CURRENT = 1
	lastwinner = -1
	lastloser = -1
	playerlist = []
	tourneylist = {'totalplayers' : 0, 'players' : []}
	tourneystats = {'entries' : 0, 'avgSF' : 0, 'winner' : {}, 'runnerup' : {}}
	seededlist = []
	activeduel = []
	statueangle = []
	statuelist = []
	unitlist = []
	adminlist = []
	blockerlist = []
	OFFICIAL = False
	STATUE = 1
	SVRDESC = False
	svr_desc = "^yTourney - Last Winner: ^r"
	SVRNAME = False
	svr_name = "^yTourney - Last Winner: ^r"

	def onPluginLoad(self, config):
		self.ms = MasterServer ()

		ini = ConfigParser.ConfigParser()
		ini.read(config)
		for (name, value) in ini.items('admin'):
			self.adminlist.append(name)
		#Don't know how to get boolean values for things in a specific section of .ini
		for (name, value) in ini.items('var'):
			if (name == "changesvrname") and (value == "true"):
				self.SVRNAME = True
			if (name == "changesvrdesc") and (value == "true"):
				self.SVRDESC = True
			if (name == "svrname"):
				self.svrname = value
			if (name == "changesvrname"):
				self.svrdesc = value
			if (name == "double") and (value == "true"):
				self.DOUBLEELIM = True

		
	def onStartServer(self, *args, **kwargs):
		print 'SERVER RESTARTED'
		self.statuelist = []
		self.STARTED = 0
		self.MINIMUM =  2
		self.RECRUIT = False
		self.ORGANIZER = -1
		self.DUELROUND = 0
		self.TOURNEYROUND = 0
		self.MISSING = -1
		self.playerlist = []
		self.tourneylist = {'totalplayers' : 0, 'players' : []}
		self.seededlist = []
		self.winnerlist = []
		self.loserlist = []
		self.activeduel = []
		self.unitlist = []
		self.counts = 4
		self.counter = 0
		f = open('winners.txt', 'r')
		self.statuelist = f.readlines()
		f.close()
			
		self.statueangle = ["0.0000 0.0000 161.7999",
				    "0.0000 0.0000 107.5998",
				    "0.0000 0.0000 53.1997",
				    "0.0000 0.0000 -22.6002",
				    "0.0000 0.0000 -63.0003",			    
				    "0.0000 0.0000 -109.2003"]

		self.blockerlist = [{'angles' : '0.0000 0.0000 -3.4000', 'name' : 'blocker1', 'position' : '7751.7021 8648.5215 -215.2963', 'scale' : '33.4070'},
				    {'angles' : '0.0000 0.0000 38.6000', 'name' : 'blocker2', 'position' : '7112.2378 8417.8262 -148.7921', 'scale' : '33.4070'},
				    {'angles' : '0.0000 0.0000 74.8001', 'name' : 'blocker3', 'position' : '6739.8462 8053.7290 -33.6641', 'scale' : '33.4070'},
				    {'angles' : '0.0000 0.0000 105.200', 'name' : 'blocker4', 'position' : '6751.2056 7424.2529 20.8391', 'scale' : '33.4070'},
				    {'angles' : '0.0000 0.0000 142.000', 'name' : 'blocker5', 'position' : '7105.5361 6935.4971 -244.8373', 'scale' : '33.4070'},
				    {'angles' : '0.0000 0.0000 176.800', 'name' : 'blocker6', 'position' : '7682.2261 6741.1899 -246.9767', 'scale' : '33.4070'},
				    {'angles' : '0.0000 0.0000 210.400', 'name' : 'blocker7', 'position' : '8237.4541 6833.5957 -14.6271', 'scale' : '33.4070'},
				    {'angles' : '0.0000 0.0000 249.200', 'name' : 'blocker8', 'position' : '8587.6348 7221.5093 -58.0270 -215.2963', 'scale' : '33.4070'},
				    {'angles' : '0.0000 0.0000 277.800', 'name' : 'blocker9', 'position' : '8664.1816 7800.2666 -182.6546', 'scale' : '33.4070'},
				    {'angles' : '0.0000 0.0000 304.200', 'name' : 'blocker10', 'position' : '8420.5273 8446.7617 -6.7577', 'scale' : '33.4070'}]
		
		self.spawnStatues(**kwargs)
		self.doBlockers('on',**kwargs)

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
		
		self.playerlist.append ({'clinum' : id, 'acctid' : 0, 'level' : 0, 'sf' : 0, 'name' : 'X', 'index' : 0, 'active' : 0, 'register' : 0, 'loses' : 0})
	
	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client ['active'] = 0
		for each in self.activeduel:
			if each['clinum'] == cli:
				self.fightersPresent(**kwargs)

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

		client ['acctid'] = int(id)
		client ['level'] = level
		client ['sf'] = sf
		client ['active'] = 1
		
		if (self.STARTED == 1) and (cli == self.MISSING):
			kwargs['Broadcast'].broadcast("set _MISSING -1")
			#self.nextDuelRound(**kwargs)
		kwargs['Broadcast'].broadcast("SendMessage %s ^cDuel Tournament made by ^yOld55 ^cand ^yPidgeoni" % (cli))
		
		if self.isAdmin(client, **kwargs):
			kwargs['Broadcast'].broadcast("SendMessage %s ^cYou are registered as an administrator for this tournament server. Send the chat message: ^rhelp ^cto see what commands you can perform." % (cli))
			
	def getPlayerIndex (self, cli):
		
		indice = -1
		for player in self.playlist:
			indice += 1
							
			if (player['clinum'] == cli):
				return indice
			
			

	def onUnitChange(self, *args, **kwargs):
		if args[1] != "Player_Commander":
			return

		cli = args[0]
		client = self.getPlayerByClientNum(cli)
				

	def RegisterScripts(self, **kwargs):
		#any extra scripts that need to go in can be done here
		#default unit list
		self.unitlist = ['Player_Savage', \
				 'Player_ShapeShifter', \
				 'Player_Predator', \
				 'Player_Hunter', \
				 'Player_Marksman']
		
		kwargs['Broadcast'].broadcast("set _green #GetIndexFromName(green_spawn)#; \
						set _red #GetIndexFromName(red_spawn)#; \
						set _exit1 #GetIndexFromName(exit1)#; \
						set _exit2 #GetIndexFromName(exit2)#; \
						set _p1x #GetPosX(|#_green|#)#; \
						set _p1y #GetPosY(|#_green|#)#; \
						set _p1z #GetPosZ(|#_green|#)#; \
						set _p2x #GetPosX(|#_red|#)#; \
						set _p2y #GetPosY(|#_red|#)#; \
						set _p2z #GetPosZ(|#_red|#)#; \
						set _e1x #GetPosX(|#_exit1|#)#; \
						set _e1y #GetPosY(|#_exit1|#)#; \
						set e1z #GetPosZ(|#_exit1|#)#; \
						set _e2x #GetPosX(|#_exit2|#)#; \
						set _e2y #GetPosY(|#_exit2|#)#; \
						set _e2z #GetPosZ(|#_exit2|#)#; \
						set _MISSING -1")		
	
		
	def isAdmin(self, client, **kwargs):
		admin = False
		
		for each in self.adminlist:
			if client['name'].lower() == each:
				admin = True
		
		return admin

	def adminCommands (self, message, client, **kwargs):
		start = re.match("start", message, flags=re.IGNORECASE)
		official = re.match("toggle official", message, flags=re.IGNORECASE)
		redo = re.match("redo", message, flags=re.IGNORECASE)
		next = re.match("next", message, flags=re.IGNORECASE)
		elim = re.match("double", message, flags=re.IGNORECASE)
		fail = re.match("remove (\S+)", message, flags=re.IGNORECASE)
		kick = re.match("kick (\S+)", message, flags=re.IGNORECASE)
		help = re.match("help", message, flags=re.IGNORECASE)
		blocker = re.match("blocker (\S+)", message, flags=re.IGNORECASE)
		cancel = re.match("cancel", message, flags=re.IGNORECASE)
		#lets admin register people, even if not official tournament
		register = re.match("register (\S+)", message, flags=re.IGNORECASE)


		if official:
			self.toggleOfficial (client, **kwargs)
		
		if redo:
			self.redoDuel (**kwargs)

		if nex:
			self.endDuel (**kwargs)

		if fail:
			killer = -1
			killed = -1

			client = self.getPlayerByName(fail.group(1))
			for each in self.activeduel:
				if each['clinum'] == client['clinum']:
					killed = each['clinum']
					each['loses'] = 3
					continue
				if each['clinum'] != client['clinum']:
				 	killer = each['clinum']
			
			if killer > -1 and killed > -1:
				self.onDeath(killer, killed, **kwargs)
				kwargs['Broadcast'].broadcast("SendMessage %s ^yAn administrator has removed you from the tournament" % (killed))

		if kick:
			reason = "An administrator has removed you from the server, probably for being annoying"
			kickclient = self.getPlayerByName(kick.group(1))
			kwargs['Broadcast'].broadcast("Kick %s \"%s\"" % (kickclient['clinum'], reason))

		if blocker:
		
			self.doBlockers(blocker.group(1), **kwargs)

		if elim:
			if self.STARTED == 1:
				kwargs['Broadcast'].broadcast("SendMessage %s A tournament has already started" % (client['clinum']))
				return
			self.toggleDouble (client, **kwargs)

		if cancel:
			self.CANCEL = True
			self.endTourney(**kwargs)
			kwargs['Broadcast'].broadcast(\
						"Serverchat The tournament has been ended by an administrator")

		if help and admin:
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s All commands on the server are done through server chat. The following are commands and a short description of what they do." % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s As an admin you must ALWAYS register yourself by sending the message: ^rregister yourname" % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^rtoggle official ^wsets the tournament between official and unofficial status.\
			 Admins MUST register people for official tournaments. Only admins can start tournaments in official mode." % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^rregister playername ^wwill register a player for the tournament. Must be used in official mode but also works in unofficial." % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^rblocker on/off ^wwill turn range blockers on/off around the arena." % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^rredo ^wwill force the players fighting in the arena to redo the last match. ONLY use after players have respawned as the next unit." % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^rremove playername ^wwill force a player to lose the match. Currently only works \
			when the player is on the server. If they have disconnected, it is best to just let them timeout." % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^rcancel ^wwill cancel the current tournament." % (client['clinum']))

	def onMessage(self, *args, **kwargs):
		
		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
		admin = self.isAdmin(client, **kwargs)
		
		#pass to admincommands
		if admin:
			self.adminCommands(message, client, **kwargs)

		#only admins are allowed to start/add/redo/etc. if the tournament is official
		if self.OFFICIAL:
			return

		roundunit = re.match("Round (\S+) Unit (\S+)", message, flags=re.IGNORECASE)
		register = re.match("register", message, flags=re.IGNORECASE)


		if start:
			self.start (client, **kwargs)

		if register:
			client = self.getPlayerByName(register.group(1))
			self.register (client, **kwargs)

		if roundunit:
			if client['clinum'] != self.ORGANIZER:
				return
			duelround = int(roundunit.group(1))
			unit = (roundunit.group(2))
			print duelround, unit
			self.unitlist[duelround-1] = ("Player_%s" % (unit))

	def doBlockers (self, toggle, **kwargs):

		if toggle == 'on':
			for each in self.blockerlist:
				kwargs['Broadcast'].broadcast(\
				"SpawnEntity Prop_Scenery model \"/world/props/tools/blocker_range.mdf\" position \"%s\" name \"%s\" angles \"%s\" scale \"%s\"" \
				% (each['position'], each['name'], each['angles'], each['scale']))

		if toggle == "off":
			for each in self.blockerlist:
				kwargs['Broadcast'].broadcast("RemoveEntity #GetIndexFromName(%s)#" % (each['name']))

		return

	def toggleOfficial (self, client, **kwargs):	
		
		if self.OFFICIAL:
			self.OFFICIAL = False
		else:
			self.OFFICIAL = True

		kwargs['Broadcast'].broadcast("SendMessage %s ^rOfficial Status: %s" % (client['clinum'], self.OFFICIAL))

	def toggleDouble (self, client, **kwargs):

		if self.DOUBLEELIM:
			self.OFFICIAL = False
		else:
			self.DOUBLEELIM = True

		kwargs['Broadcast'].broadcast("SendMessage %s ^rDouble Elimination Status: %s" % (client['clinum'], self.DOUBLEELIM))

	def redoDuel (self, **kwargs):	

		self.DUELROUND -= 1
		
		for each in self.activeduel:
			if (each['clinum'] == self.lastloser):
				each['loses'] -= 1
									
			if (each['clinum'] == self.lastwinner):
				each['wins'] -= 1
				kwargs['Broadcast'].broadcast("ExecScript GlobalSet var R%sS%s val %s" % (each['bracket'], each['column'], each['wins']))
				kwargs['Broadcast'].broadcast("ExecScript GlobalSync")
		
		kwargs['Broadcast'].broadcast("set _DUELER1 -1; set _DUELER2 -1")
		self.nextDuelRound(**kwargs)

	def start (self, client, **kwargs):

		admin = self.isAdmin(client, **kwargs)
				
		if self.RECRUIT or self.STARTED == 1:
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^rA tournament has already been started. You must wait till the current tournament ends to start a new one." % (client['clinum']))
			return

		activeplayers = 0
		for player in self.playerlist:
			if player['active'] == 1:
				activeplayers += 1

		if (activeplayers < self.MINIMUM):
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^rA minimum of two active players is required to call a tournament" % (client['clinum']))		
			return
		
		self.RegisterScripts(**kwargs)	
		self.RECRUIT = True
		kwargs['Broadcast'].broadcast(\
		"ServerChat ^r%s ^chas started a tournament! To join the tournament, send the message 'register' to ALL, SQUAD, or TEAM chat.; \
		 ExecScript starttourney; \
		 ExecScript GlobalSet var TSB val %s; \
		 ExecScript GlobalShowDuel" \
		 % (client['name'], client['name']))

		self.ORGANIZER = client['clinum']
		kwargs['Broadcast'].broadcast("ClientExecScript %s ClientShowOptions" % (self.ORGANIZER))
	

	def register (self, client, **kwargs):

		kwargs['Broadcast'].broadcast("TakeItem #GetIndexFromClientNum(%s)# 10" % (client ['clinum']))

		if self.RECRUIT and client['register'] == 0:
			self.tourneylist ['players'].append ({'clinum' : client['clinum'],
							      'acctid' : client['acctid'],
							      'name' : client['name'],
							      'sf' : client['sf'],
							      'level' : client['level'],
							      'totalwins' : 0,
							      'totalloses' : 0,
							      'seed' : 0,
							      'advance' : 2,
							      'bye' : 0,
							      'bracket' : 0})	
			client['register'] = 1
			self.tourneylist ['totalplayers'] += 1
			kwargs['Broadcast'].broadcast(\
			"Serverchat ^r%s ^chas registered for the tournament." % (client ['name']))
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^yYou have successfully registered for the tournament." % (client ['clinum']))
			
		else:

			return

	def RegisterStart(self, **kwargs):

		self.RECRUIT = False
		self.STARTED = 1
		self.seedPlayers(**kwargs)
	
	def getTourneyinfo(self, **kwargs):

		entries = self.seededlist['totalplayers']
		self.tourneystats['entries'] = entries
		totalsf = 0

		for each in self.seededlist['players']:
			totalsf += each['sf']

		self.tourneystats['avgSF'] = int(totalsf/entries)


	def seedPlayers(self, **kwargs):
		
		self.TOURNEYROUND = 1
		kwargs['Broadcast'].broadcast(\
		"ExecScript GlobalSet var TR val 1")
		kwargs['Broadcast'].broadcast(\
		"ClientExecScript %s ClientHideOptions" % (self.ORGANIZER))
		if (self.tourneylist ['totalplayers'] < 4):
			self.tourneylist = {'totalplayers' : 0, 'players' : []}
			self.seededlist = []
			self.STARTED = 0
			self.ORGANIZER = -1
			self.RECRUIT = False
			for each in self.playerlist:
				each['register'] = 0
		
			kwargs['Broadcast'].broadcast(\
			"ClientExecScript -1 ClientClear")
			kwargs['Broadcast'].broadcast(\
			"Serverchat The tournament must have 4 people to start. Aborting.")
			
			return

		self.seededlist = sorted(self.tourneylist ['players'], key=itemgetter('sf', 'level', 'clinum'), reverse=True)
		seed = 0

		#Gets information about tournament for scoring purposes
		self.getTourneyinfo()

		for player in self.seededlist:
			seed += 1
			player['seed'] += seed

		totalplayers = self.tourneylist['totalplayers']
		start = 0
		end = totalplayers - 1

		#round 1 seeding/bracket placement
		if (self.tourneylist['totalplayers'] % (2)) == 0:
	
			total_brackets = (totalplayers / 2)
			bracket = 1

			while (start < total_brackets):
				self.seededlist[start]['bracket'] = bracket
				self.seededlist[end]['bracket'] = bracket
				kwargs['Broadcast'].broadcast(\
				"ExecScript GlobalSet var R%sNA val %s;\
				 ExecScript GlobalSet var R%sFA val %s;\
				 ExecScript GlobalSet var R%sNB val %s;\
				 ExecScript GlobalSet var R%sFB val %s;"\
				 % (bracket, self.seededlist[start]['name'],bracket,self.seededlist[start]['sf'],bracket,self.seededlist[end]['name'],bracket,self.seededlist[end]['sf']))	
				start += 1
				end -= 1
				bracket += 1

		if (self.tourneylist['totalplayers'] % (2)) != 0:
			totalplayers = totalplayers+1 
			total_brackets = (totalplayers / 2)
			bracket = 1
			self.seededlist[start]['bye'] = 1
			self.seededlist[start]['bracket'] = bracket
			self.seededlist[start]['advance'] = 1
			self.winnerlist.append(self.seededlist[start])
			print self.winnerlist

			kwargs['Broadcast'].broadcast(\
			"ExecScript GlobalSet var R%sSA val 3;\
			 ExecScript GlobalSet var R%sNA val %s;\
			 ExecScript GlobalSet var R%sFA val %s;\
			 ExecScript GlobalSet var R%sNB val BYE"\
			 % (bracket,bracket,self.seededlist[start]['name'],bracket,self.seededlist[start]['sf'],bracket))
			start += 1
			bracket += 1

			while (start < total_brackets):
				self.seededlist[start]['bracket'] = bracket
				self.seededlist[end]['bracket'] = bracket
				kwargs['Broadcast'].broadcast(\
				"ExecScript GlobalSet var R%sNA val %s;\
				 ExecScript GlobalSet var R%sFA val %s; \
				 ExecScript GlobalSet var R%sNB val %s; \
				 ExecScript GlobalSet var R%sFB val %s;"\
				 % (bracket,self.seededlist[start]['name'],bracket,self.seededlist[start]['sf'],bracket,self.seededlist[end]['name'],bracket,self.seededlist[end]['sf']))
				bracket += 1
				start += 1
				end -= 1

		
		self.checkRound(**kwargs)
		

	def checkRound(self, **kwargs):
		#figure out who has yet to fight
		print 'at checkRound'
		bl = []
		for brackets in self.seededlist:
			bl.append(brackets['bracket'])
		print bl

		for item in set(bl):
			if (bl.count(item) > 1):
				print item
				self.nextDuel(item, **kwargs)
				return
			
		self.nextRound(**kwargs)
		print 'round over'
		self.TOURNEYROUND += 1

	def nextDuel(self, bracket, **kwargs):
		print bracket
		kwargs['Broadcast'].broadcast(\
		"ExecScript GlobalSet var CR val %s;\
		 ExecScript GlobalSync"\
		 % (bracket))

		for each in self.seededlist:
			if each['bracket'] == bracket:
				#added to kill each of the duelers before the start so they get out of their current duels
				kwargs['Broadcast'].broadcast(\
				"set _index #GetIndexFromClientNum(%s)#;\
				 KillEntity #_index#"\
				 % (each['clinum']))
				self.activeduel.append(each)

		for each in self.activeduel:
			each['loses'] = 0
			each['wins'] = 0

		self.activeduel[0]['column'] = "A"
		self.activeduel[1]['column'] = "B"
		
		self.getNextDuel(**kwargs)

	def getNextDuel(self, *args, **kwargs):
		self.nextDuelRound(**kwargs)

	def nextDuelRound(self, **kwargs):
		
		if self.fightersPresent(**kwargs):
			kwargs['Broadcast'].broadcast("set _DUEL 0")
			self.getUnit(**kwargs)
			kwargs['Broadcast'].broadcast(\
			"set _index #GetIndexFromClientNum(%s)#;\
			 GiveItem #_index# 9 Spell_CommanderHeal;\
			 StartEffectOnObject #_index# \"shared/effects/green_aura.effect\";\
			 ResetAttributes #_index#;\
			 SetPosition #_index# #_p1x# #_p1y# #_p1z#;\
			 ChangeUnit #_index# #_UNIT# true false false false false false false;\
			 ClientExecScript %s holdmove"\
			 % (self.activeduel[0]['clinum'],self.activeduel[0]['clinum']))

			kwargs['Broadcast'].broadcast(\
			"set _index #GetIndexFromClientNum(%s)#;\
			 GiveItem #_index# 9 Spell_CommanderHeal;\
			 StartEffectOnObject #_index# \"shared/effects/red_aura.effect\"; \
			 ResetAttributes #_index#; \
			 SetPosition #_index# #_p2x# #_p2y# #_p2z#;\
			 ChangeUnit #_index# #_UNIT# true false false false false false false;\
			 ClientExecScript %s holdmove"\
			 % (self.activeduel[1]['clinum'],self.activeduel[1]['clinum']))

			kwargs['Broadcast'].broadcast(\
			"ExecScript setdueler dueler1 %s dueler2 %s"\
			 % (self.activeduel[0]['clinum'], self.activeduel[1]['clinum']))

			kwargs['Broadcast'].broadcast(\
			"Execscript duelcountdown")	
		else:
			
			print 'player missing'

	def waitForPlayer(self, *args, **kwargs):
		action = args[0]

		if (action == 'Timeout'):
			for each in self.activeduel:
				if each['clinum'] == self.MISSING:
					each['loses'] = 3
					missing = each['clinum']
					self.MISSING = -1
				else:
					remaining = each['clinum']
			self.onDeath(remaining, missing,**kwargs)
					
		if (action == 'Connected'):
			#if (self.DUELROUND > 0):
				#self.DUELROUND -= 1
			self.MISSING = -1
			kwargs['Broadcast'].broadcast("set _DUELER1 -1; set _DUELER2 -1")
			self.nextDuelRound(**kwargs)					
			
	def getUnit(self, **kwargs):
		
		unit = self.unitlist[self.DUELROUND]
		kwargs['Broadcast'].broadcast("set _UNIT %s" % (unit))

	def fightersPresent(self, **kwargs):
		
		if self.MISSING > -1:
			return False
		
		for each in self.activeduel:
			clinum = each['clinum']
			for players in self.playerlist:
				if (players['clinum'] == clinum) and (players['active'] == 0):
					self.MISSING = players['clinum']
					name = players['name']
					kwargs['Broadcast'].broadcast(\
					"ServerChat ^cThe next duel is between ^r%s ^cand ^r%s^c, but ^r%s ^chas disconnected. They have 1 minute to reconnect or they will lose the round.;\
					 set _MISSING %s;\
					 ExecScript missingfighter"\
					 % (self.activeduel[0]['name'],self.activeduel[1]['name'], name, self.MISSING))
					return False
		return True

	def onDeath(self, *args, **kwargs):
		print 'got Death'
		#this will be called from a specific filter
		killer = args[0]
		killed = args[1]
		wasduel = 0
		print args
		if self.STARTED != 1 or self.MISSING > -1:
			return
		
		for each in self.activeduel:
			if (each['clinum'] == killed):
				wasduel += 1
				clikilled = each
			if (each['clinum'] == killer):
				wasduel += 1
				clikill = each

		if wasduel == 2:
			self.DUELROUND += 1
			self.lastloser = clikilled['clinum']
			clikilled['loses'] += 1
			kwargs['Broadcast'].broadcast(\
			"set _idx #GetIndexFromClientNum(%s)#;\
			 TakeItem #_idx# 9;\
			 set _DUELER1 -1;\
			 set _DUELER2 -1"\
			 % (clikilled['clinum']))

			self.lastwinner = clikill['clinum']
			clikill['wins'] += 1
			kwargs['Broadcast'].broadcast(\
			"ExecScript GlobalSet var R%sS%s val %s;\
			 ExecScript GlobalSync"\
			 % (clikill['bracket'], clikill['column'], clikill['wins']))
					
			for each in self.activeduel:		
				if each['loses'] > 2:
					self.checkendDuel(**kwargs)
					kwargs['Broadcast'].broadcast("ExecScript GlobalSync")
					return
	
			kwargs['Broadcast'].broadcast("ExecScript nextduelround")
		
	def checkendDuel(self, **kwargs):
		kwargs['Broadcast'].broadcast(\
		"set _index #GetIndexFromClientNum(%s)#;\
		 StopEffectOnObject #_index# \"shared/effects/green_aura.effect\";\
		 SetPosition #_index# #_e1x# #_e1y# #_e1z#;\
		 ChangeUnit #_index# Player_Savage  true false false false false false false"\
		 % (self.activeduel[0]['clinum']))

		kwargs['Broadcast'].broadcast(\
		"set _index #GetIndexFromClientNum(%s)#;\
		 StopEffectOnObject #_index# \"shared/effects/red_aura.effect\";\
		 SetPosition #_index# #_e2x# #_e2y# #_e2z#;\
		 ChangeUnit #_index# Player_Savage  true false false false false false false"\
		 % (self.activeduel[1]['clinum']))

		if not self.OFFICIAL:
			self.endDuel(**kwargs)
			return

		if self.OFFICIAL:
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s This duel is over. Please send message 'next' to chat for the next duel, or 'redo' if there was an error."\
			 % (self.ORGANIZER))			
			
	def endDuel(self, **kwargs):
	
		for each in self.activeduel:
				if each['loses'] > 2:
					loser = each['name']
					clinum = each['clinum']
					each['totalloses'] += 1
					self.loserlist.append(each)
					self.tourneystats['runnerup'] = { 'name' : each['name'], 'acctid' : each['acctid'] }
					self.removePlayer(each['clinum'])
				if each['loses'] < 3:
					winner = each['name']
					self.tourneystats['winner'] = { 'name' : each['name'], 'acctid' : each['acctid'] }
					each['totalwins'] += 1
					if each['totalloses'] == 0:
						self.winnerlist.append(each)
					if each['totalloses'] == 1:
						self.loserlist.append(each)
		kwargs['Broadcast'].broadcast(\
		"ServerChat ^y%s ^chas defeated ^y%s ^cand moves on to the next round"\
		 % (winner, loser))

		self.activeduel = []
		self.DUELROUND = 0
		
		self.checkRound(**kwargs)

	def swapList(self, winners, losers, **kwargs):
		
		#gets if we are currently in winners or losers bracket, 1 = winner 2 = losers
		
		#special condition, all remaining players are in losers bracket
		if winners == 0:
			print 'condition: no winners'
			self.CURRENT = 2
			self.seededlist = list(self.loserlist)
			del self.loserlist[:]
			return

		#special condition, all are in winners bracket
		if losers == 0:
			print 'condition: no losers'
			self.CURRENT = 1
			self.seededlist = list(self.winnerlist)
			del self.winnerlist[:]
			return

		#special condition, split brackets
		if losers == 1 and winners == 1:
			print 'condition: split lists'
			self.seededlist = [self.winnerlist[0], self.loserlist[0]]
			del self.loserlist[:]
			del self.winnerlist[:]
			return		

		if self.CURRENT == 1:
			if losers > 1:
				print 'condition: start loser bracket'
				self.CURRENT = 2
				self.seededlist = list(self.loserlist)
				self.loserlist = []
				return
			elif losers < 2:
				self.CURRENT = 1
				self.seededlist = list(self.winnerlist)
				self.winnerlist = []
				return
		if self.CURRENT == 2:
			if winners > 1:
				print 'condition: start winner bracket'
				self.CURRENT = 1
				self.seededlist = list(self.winnerlist)
				self.winnerlist = []
				return
			elif winners < 2:
				self.CURRENT = 2
				self.seededlist = list(self.loserlist)
				self.loserlist = []
				return
		
		print self.seededlist
				
	def nextRound(self, **kwargs):
		kwargs['Broadcast'].broadcast("ExecScript GlobalClear; ClientExecScript -1 releasemove")
		
		print 'made it to nextRound'
		remaining = 0
		self.TOURNEYROUND += 1
		kwargs['Broadcast'].broadcast("ExecScript GlobalSet var TR val %s" % (self.TOURNEYROUND))
		
					
		if self.DOUBLEELIM:
			
			winners = self.getRemaining(self.winnerlist, **kwargs)
			losers = self.getRemaining(self.loserlist, **kwargs)
			remaining = winners + losers
			if remaining == 1:
				self.endTourney(**kwargs)
				return
			print winners, losers
			self.swapList(winners, losers)

		remaining = self.getRemaining(self.seededlist, **kwargs)
		kwargs['Broadcast'].broadcast("echo Remaining players: %s" % (remaining))
		if (remaining == 1):
			self.endTourney(**kwargs)		
			return

		if (remaining % (2)) != 0:
			self.getBye(**kwargs)
		
		self.seededlist = sorted(self.seededlist, key=itemgetter('advance', 'bracket'))

		#re-seed the list if we are switching to the loser bracket
		if self.CURRENT == 2:
			self.seededlist = sorted(self.seededlist, key=itemgetter('advance', 'seed', 'bracket'))

		#now to do the re-bracketing
		start = 0
		end = remaining - 1
		doround = True
		bracket = 0

		if (self.seededlist[start]['advance'] == 1):
			bracket = 1
			byer = self.seededlist[start]
			byer['bracket'] = bracket
			if byer['totalloses'] == 1:
				self.loserlist.append(self.seededlist[start])
			if byer['totalloses'] == 0:
				self.winnerlist.append(self.seededlist[start])
			kwargs['Broadcast'].broadcast(\
			"ExecScript GlobalSet var R%sSA val 3;\
			 ExecScript GlobalSet var R%sNA val %s;\
			 ExecScript GlobalSet var R%sFA val %s;\
			 ExecScript GlobalSet var R%sNB val BYE"\
			 % (bracket,bracket,self.seededlist[start]['name'],bracket,self.seededlist[start]['sf'],bracket))
			self.seededlist[start]['column'] = 'A'
			start += 1
		
		
		while doround:
			bracket += 1	
			self.seededlist[start]['bracket'] = bracket
			self.seededlist[end]['bracket'] = bracket
			kwargs['Broadcast'].broadcast(\
			"ExecScript GlobalSet var R%sNA val %s;\
			 ExecScript GlobalSet var R%sFA val %s;\
			 ExecScript GlobalSet var R%sNB val %s;\
			 ExecScript GlobalSet var R%sFB val %s;"\
			 % (bracket,self.seededlist[start]['name'],bracket,self.seededlist[start]['sf'],bracket,self.seededlist[end]['name'],bracket,self.seededlist[end]['sf']))
			self.seededlist[start]['column'] = "A"
			self.seededlist[end]['column'] = "B"
			if (end - start) == 1:
				doround = False
			start += 1
			end -= 1

		print self.seededlist
		self.checkRound(**kwargs)

	def getRemaining(self, getlist, **kwargs):
		remaining = 0

		for each in getlist:
			each['advance'] = 2
			remaining += 1

		return remaining

	def endTourney(self, **kwargs):

		if not self.CANCEL:
			winner = self.seededlist[0]
			name = winner['name']
			clinum = winner['clinum']
			wins = winner['totalwins']

			kwargs['Broadcast'].broadcast(\
			"ServerChat ^cThis tournament is over! The winner is %s with a total of %s wins."\
			 % (name, wins))

			kwargs['Broadcast'].broadcast(\
			"set _winnerind #GetIndexFromClientNum(%s);\
			 ClientExecScript %s ClientHideOptions"\
			 % (clinum, self.ORGANIZER))

			if self.SVRDESC:
				kwargs['Broadcast'].broadcast(\
				"set svr_desc \"%s\"%s" % (self.svr_desc, name))
			if self.SVRNAME:
				kwargs['Broadcast'].broadcast(\
				"set svr_name \"%s\"%s"\
				 % (self.svr_name, name))
			#Adds a statue
			kwargs['Broadcast'].broadcast(\
			"RemoveEntity #GetIndexFromName(player_%s)#;\
			 SpawnEntityAtEntity statue_%s Prop_Dynamic name player_%s maxhealth 999999999 model \"/world/props/arena/stone_legionnaire.mdf\" angles \"%s\" team 0 seed 0 scale 1.7627 propname %s"\
			 % (self.STATUE,self.STATUE,self.STATUE,self.statueangle[self.STATUE-1],name))
			self.STATUE += 1
			if self.STATUE > 6:
				self.STATUE = 1
			#add name to statue list
			self.statuelist.append(name)
			
			#Truncate statuelist to 6 winners
			size = len(self.statuelist)
			if size > 5:
				del self.statuelist[0]
			#writes file, winners.txt
			f = open('winners.txt', 'w')
			for each in self.statuelist:
				f.write("%s" % (each))
			f.close()
			
		self.tourneylist = {'totalplayers' : 0, 'players' : []}
		self.seededlist = []
		self.winnerlist = []
		self.loserlist = []
		self.activeduel = []
		self.CURRENT = 1
		self.STARTED = 0
		self.ORGANIZER = -1
		self.RECRUIT = False
		self.TOURNEYROUND = 0
		self.MISSING = -1
		self.CANCEL = False
		for each in self.playerlist:
			each['register'] = 0
		
		kwargs['Broadcast'].broadcast(\
		"ExecScript GlobalSet var TR val 0;\
		 ExecScript GlobalClear; ExecScript GlobalSync")

	def getBye(self, **kwargs):
		#give the bye to the highest seeded player that doesn't have a bye
		lowest = -1
		pick = None
		for each in self.seededlist:
			if each['bye'] == 1:
				continue
				
			ltarget = each['seed']
			if (lowest < 0):
				lowest = ltarget
				# wouldn't work if the first player was the one to pick, so had to do this here
				pick = each
				continue
			if (lowest < ltarget):
				continue
			lowest = ltarget
			pick = each

		print pick
		pick['bye'] = 1
		pick['advance'] = 1

	def removePlayer(self, clinum, **kwargs):
		#remove a player when they have been defeated, if double elimination they have been moved to self.loserlist with single loss.
		for each in self.seededlist:
			if each['clinum'] == clinum:
				self.seededlist.remove(each)
		#for double elimination, remove them all together if they have two loses
		for each in self.loserlist:
			if each['clinum'] == clinum:
				if each['totalloses'] > 1:
					self.loserlist.remove(each)

	def spawnStatues(self, **kwargs):
		for each in self.statuelist:
			kwargs['Broadcast'].broadcast(\
			"RemoveEntity #GetIndexFromName(player_%s)#;\
			 SpawnEntityAtEntity statue_%s Prop_Dynamic name player_%s maxhealth 999999999 model \"/world/props/arena/stone_legionnaire.mdf\" angles \"%s\" team 0 seed 0 scale 1.7627 propname %s"\
			 % (self.STATUE,self.STATUE,self.STATUE,self.statueangle[self.STATUE-1],each))

			self.STATUE += 1
			if self.STATUE > 6:
				self.STATUE = 1
					
