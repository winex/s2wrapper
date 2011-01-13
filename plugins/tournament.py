# -*- coding: utf-8 -*-
# 12/22/10 - Added end of game balance report, VERSION 1.0.1 (first version stamp, so arbitrary)
import re
import math
import time
import ConfigParser
import threading
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler
from repeattimer import RepeatTimer
from operator import itemgetter
from threading import Timer

#This plugin was written by Old55 and he takes full responsibility for the junk below.
#He does not know python so the goal was to make something functional, not something
#efficient or pretty.

#NORMAL VERSION


class tournament(ConsolePlugin):
	VERSION = "0.0.1"
	STARTED = 0
	MINIMUM =  2
	RECRUIT = False
	ORGANIZER = -1
	DUELROUND = 0
	TOURNEYROUND = 0
	MISSING = -1
	playerlist = []
	tourneylist = {'totalplayers' : 0, 'players' : []}
	seededlist = []
	activeduel = []
	unitlist = []
	counts = 4
	counter = 0
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

	def onStartServer(self, *args, **kwargs):
		print 'SERVER RESTARTED'
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
		self.activeduel = []
		self.unitlist = []
		self.counts = 4
		self.counter = 0

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
		print ip
		reason = "You are banned from this server"
		#Kicks Brewen
		if (ip == "76.177.233.35"):
			kwargs['Broadcast'].broadcast("kick %s \"%s\"" % (id, reason))

		for client in self.playerlist:
			if (client['clinum'] == id):
				
								
				return
		self.playerlist.append ({'clinum' : id, 'acctid' : 0, 'level' : 0, 'sf' : 0, 'name' : 'X', 'index' : 0, 'active' : 1, 'register' : 0})

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
		#these are for identifying bought and sold items
		self.unitlist = ['Player_Savage', 'Player_ShapeShifter', 'Player_Predator', 'Player_Hunter', 'Player_Chaplain']
		kwargs['Broadcast'].broadcast("set _green #GetIndexFromName(green_spawn)#; set _red #GetIndexFromName(red_spawn)#; set _exit1 #GetIndexFromName(exit1)#; set _exit2 #GetIndexFromName(exit2)#; set _p1x #GetPosX(|#_green|#)#; set _p1y #GetPosY(|#_green|#)#; set _p1z #GetPosZ(|#_green|#)#; set _p2x #GetPosX(|#_red|#)#; set _p2y #GetPosY(|#_red|#)#; set _p2z #GetPosZ(|#_red|#)#; set _e1x #GetPosX(|#_exit1|#)#; set _e1y #GetPosY(|#_exit1|#)#; set e1z #GetPosZ(|#_exit1|#)#; set _e2x #GetPosX(|#_exit2|#)#; set _e2y #GetPosY(|#_exit2|#)#; set _e2z #GetPosZ(|#_exit2|#)#; set _MISSING -1")
		#kwargs['Broadcast'].broadcast("")
		
		

	def retrieveIndex(self, mover, action, **kwargs):
		#Use this for any manipulations when you need to get the current player index from the server. This is used for MOVE, PREVENT, ALLOW
		cli = mover['clinum']
		client = self.getPlayerByClientNum(cli)
		kwargs['Broadcast'].broadcast("set _value #GetIndexFromClientNum(%s)#; echo Sv: Client %s index is #_value#. ACTION: %s" % (cli, cli, action))

	def onRetrieveIndex(self, *args, **kwargs):
		#get stuff from parser
		clinum = args[0]
		index = args[1]
		action = args[2]
		if (action == 'MOVE'):
			self.move(clinum, index, **kwargs)
		if (action == 'PREVENT'):
			self.prevent(clinum, index, **kwargs)
		if (action == 'ALLOW'):
			self.allow(clinum, index, **kwargs)
		

	def onMessage(self, *args, **kwargs):
		
		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
		
		start = re.match("start", message, flags=re.IGNORECASE)		
		register = re.match("register", message, flags=re.IGNORECASE)
		if start:
			self.start (client, **kwargs)
		if register:
			self.register (client, **kwargs)
		
	def start (self, client, **kwargs):
		
		if self.RECRUIT or self.STARTED == 1:
			kwargs['Broadcast'].broadcast("SendMessage %s ^rA tournament has already been started. You must wait till the current tournament ends to start a new one." % (client['clinum']))
			return

		activeplayers = 0
		for player in self.playerlist:
			if player['active'] == 1:
				activeplayers += 1

		if (activeplayers < self.MINIMUM):
			kwargs['Broadcast'].broadcast("SendMessage %s ^rA minimum of eight active players is required to call a tournament" % (client['clinum']))		
			return
		
		self.RegisterScripts(**kwargs)	
		self.RECRUIT = True
		kwargs['Broadcast'].broadcast("ServerChat ^r%s ^chas started a tournament! To join the tournament, send the message 'register' to ALL, SQUAD, or TEAM chat.; ExecScript starttourney; ExecScript GlobalSet var TSB val %s; ExecScript GlobalShowDuel" % (client['name'], client['name']))
		self.ORGANIZER = client['clinum']
		#kwargs['Broadcast'].broadcast("ClientExecScript %s organize" % (client['clinum']))
		#self.counter = 3
		#kwargs['Broadcast'].broadcast("Serverchat ^cYou have %s minutes left to register for the next tournament by sending the message 'register' in game chat." % (self.counter))
		#threading.thread(self.RegisterStart(**kwargs))
		

	def register (self, client, **kwargs):

		if self.RECRUIT and client['register'] == 0:
			self.tourneylist ['players'].append ({'clinum' : client['clinum'], 'name' : client['name'], 'sf' : client['sf'], 'level' : client['level'], 'totalwins' : 0, 'seed' : 0, 'advance' : 2, 'bye' : 0, 'bracket' : 0})	
			client['register'] = 1
			self.tourneylist ['totalplayers'] += 1
			kwargs['Broadcast'].broadcast("Serverchat ^r%s ^chas registered for the tournament." % (client ['name']))
			kwargs['Broadcast'].broadcast("SendMessage %s ^yYou have successfully registered for the tournament." % (client ['clinum']))
		else:

			return

	def RegisterStart(self, **kwargs):
		self.RECRUIT = False
		self.STARTED = 1
		self.SeedPlayers(**kwargs)
		
	def SeedPlayers(self, **kwargs):

		self.TOURNEYROUND = 1
		kwargs['Broadcast'].broadcast("ExecScript GlobalSet var TR val 1")
		if (self.tourneylist ['totalplayers'] < 2):
			self.tourneylist = {'totalplayers' : 0, 'players' : []}
			self.seededlist = []
			self.STARTED = 0
			self.ORGANIZER = -1
			self.RECRUIT = False
			for each in self.playerlist:
				each['register'] = 0
		
			kwargs['Broadcast'].broadcast("ClientExecScript -1 ClientClear")
			kwargs['Broadcast'].broadcast("Serverchat The tournament must have 3 people to start. Aborting.")
			#self.endTourney(**kwargs)
			return

		self.seededlist = sorted(self.tourneylist ['players'], key=itemgetter('sf', 'level', 'clinum'), reverse=True)
		seed = 0
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
				kwargs['Broadcast'].broadcast("ExecScript GlobalSet var R%sNA val %s; ExecScript GlobalSet var R%sFA val %s; ExecScript GlobalSet var R%sNB val %s; ExecScript GlobalSet var R%sFB val %s;" % (bracket, self.seededlist[start]['name'],bracket,self.seededlist[start]['sf'],bracket,self.seededlist[end]['name'],bracket,self.seededlist[end]['sf']))	
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
			kwargs['Broadcast'].broadcast("ExecScript GlobalSet var R%sSA val 3; ExecScript GlobalSet var R%sNA val %s; ExecScript GlobalSet var R%sFA val %s; ExecScript GlobalSet var R%sNB val BYE" % (bracket,bracket,self.seededlist[start]['name'],bracket,self.seededlist[start]['sf'],bracket))
			start += 1
			bracket += 1
			while (start < total_brackets):
				self.seededlist[start]['bracket'] = bracket
				self.seededlist[end]['bracket'] = bracket
				kwargs['Broadcast'].broadcast("ExecScript GlobalSet var R%sNA val %s; ExecScript GlobalSet var R%sFA val %s;ExecScript GlobalSet var R%sNB val %s; ExecScript GlobalSet var R%sFB val %s;" % (bracket,self.seededlist[start]['name'],bracket,self.seededlist[start]['sf'],bracket,self.seededlist[end]['name'],bracket,self.seededlist[end]['sf']))
				bracket += 1
				start += 1
				end -= 1

		kwargs['Broadcast'].broadcast("Serverchat ^cThe tournament seeding is as follows:")
		kwargs['Broadcast'].broadcast("ExecScript GlobalSet var CR val 1; ExecScript GlobalSync; ")
		for each in self.seededlist:
			kwargs['Broadcast'].broadcast("Serverchat ^cSeed: ^y%s ^cPlayer: ^y%s ^cSF: ^y%s" % (each['seed'], each['name'], each['sf']))
		
		
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
		kwargs['Broadcast'].broadcast("ExecScript GlobalSet var CR val %s; ExecScript GlobalSync" % (bracket))

		for each in self.seededlist:
			if each['bracket'] == bracket:
				#added to kill each of the duelers before the start so they get out of their current duels
				kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; KillEntity #_index#" % (each['clinum']))
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
			
			self.getUnit(**kwargs)
			kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; ResetAttributes #_index#; SetPosition #_index# #_p1x# #_p1y# #_p1z#; ChangeUnit #_index# #_UNIT# true false false false false false false; ClientExecScript %s holdmove; set _DUELER1 %s;" % (self.activeduel[0]['clinum'],self.activeduel[0]['clinum'], self.activeduel[0]['clinum']))
			kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#;  ResetAttributes #_index#; SetPosition #_index# #_p2x# #_p2y# #_p2z#; ChangeUnit #_index# #_UNIT# true false false false false false false; ClientExecScript %s holdmove; set _DUELER2 %s;" % (self.activeduel[1]['clinum'],self.activeduel[1]['clinum'],self.activeduel[1]['clinum']))
			self.DUELROUND += 1	
		else:
			
			print 'player missing'

	def waitForPlayer(self, *args, **kwargs):
		action = args[0]

		if (action == 'Timeout'):
			for each in self.activeduel:
				if each['clinum'] == self.MISSING:
					each['loses'] = 3
					self.MISSING = -1
					self.onDeath(-1, each['clinum'],**kwargs)
					
		if (action == 'Connected'):
			if (self.DUELROUND > 0):
				self.DUELROUND -= 1
			self.nextDuelRound(**kwargs)					
		
	def getUnit(self, **kwargs):
		
		unit = self.unitlist[self.DUELROUND]
		kwargs['Broadcast'].broadcast("set _UNIT %s" % (unit))

	def fightersPresent(self, **kwargs):

		for each in self.activeduel:
			clinum = each['clinum']
			for players in self.playerlist:
				if (players['clinum'] == clinum) and (players['active'] == 0):
					self.MISSING = players['clinum']
					name = players['name']
					kwargs['Broadcast'].broadcast("ServerChat ^cThe next duel is between ^r%s ^cand ^r%s^c, but ^r%s has disconnected. They have 2 minutes to reconnect or they will lose the round.; set _MISSING %s; ExecScript missingfighter" % (self.activeduel[0]['name'],self.activeduel[1]['name'], name, self.MISSING))
					return False
		return True

	def onDeath(self, *args, **kwargs):
		print 'got Death'
		#this will be called from a specific filter
		killer = args[0]
		killed = args[1]
		print args

		if self.STARTED == 1:
			for each in self.activeduel:
				if (each['clinum'] == killed):
					each['loses'] += 1
					kwargs['Broadcast'].broadcast("set _idx #GetIndexFromClientNum(%s)#; TakeItem #_idx# 9; set _DUELER1 -1; set _DUELER2 -1" % (each['clinum']))

				if (each['clinum'] == killer):
					each['wins'] += 1
					kwargs['Broadcast'].broadcast("ExecScript GlobalSet var R%sS%s val %s; ExecScript GlobalSync" % (each['bracket'], each['column'], each['wins']))
			
			for each in self.activeduel:		
				if each['loses'] > 2:
					self.endDuel(**kwargs)
					kwargs['Broadcast'].broadcast("ExecScript GlobalSync")
					return

			if (killer == self.activeduel[0]['clinum']) or (killer == self.activeduel[1]['clinum']):
				if (self.activeduel[0]['wins']) < 3 and (self.activeduel[1]['wins'] < 3):
					kwargs['Broadcast'].broadcast("ExecScript nextduelround")
		
	def endDuel(self, **kwargs):
		kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; SetPosition #_index# #_e1x# #_e1y# #_e1z#; KillEntity #_index#" % (self.activeduel[0]['clinum']))
		kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; SetPosition #_index# #_e2x# #_e2y# #_e2z#; KillEntity #_index#" % (self.activeduel[1]['clinum']))

		for each in self.activeduel:
			if each['loses'] > 2:
				loser = each['name']
				clinum = each['clinum']
				self.removePlayer(each['clinum'])
			if each['loses'] < 3:
				winner = each['name']

		kwargs['Broadcast'].broadcast("ServerChat ^r%s has defeated ^r%s and moves on to the next round" % (winner, loser))

		self.activeduel = []
		self.DUELROUND = 0
		self.checkRound(**kwargs)
		

	def nextRound(self, **kwargs):
		kwargs['Broadcast'].broadcast("ExecScript GlobalClear")
		print 'made it to nextRound'
		remaining = 0
		self.TOURNEYROUND += 1
		for each in self.seededlist:
			each['advance'] = 2
			each['totalwins'] += 1
			remaining += 1
		if (remaining == 1):
			self.endTourney(**kwargs)		
			return
		if (remaining % (2)) != 0:
			self.getBye(**kwargs)
		
		self.seededlist = sorted(self.seededlist, key=itemgetter('advance', 'bracket'))

		#now to do the re-bracketing
		start = 0
		end = remaining - 1
		doround = True

		if (self.seededlist[start]['advance'] == 1):
			bracket = self.seededlist[start]['bracket']
			kwargs['Broadcast'].broadcast("ExecScript GlobalSet var R%sSA val 3; ExecScript GlobalSet var R%sNA val %s; ExecScript GlobalSet var R%sFA val %s; ExecScript GlobalSet var R%sNB val BYE" % (bracket,bracket,self.seededlist[start]['name'],bracket,self.seededlist[start]['sf'],bracket))
			start += 1
		
		
		while doround:	
			bracket = self.seededlist[start]['bracket']
			self.seededlist[end]['bracket'] = bracket
			kwargs['Broadcast'].broadcast("ExecScript GlobalSet var R%sNA val %s; ExecScript GlobalSet var R%sFA val %s;ExecScript GlobalSet var R%sNB val %s;ExecScript GlobalSet var R%sFB val %s;" % (bracket,self.seededlist[start]['name'],bracket,self.seededlist[start]['sf'],bracket,self.seededlist[end]['name'],bracket,self.seededlist[end]['sf']))
			if (end - start) == 1:
				doround = False
			start += 1
			end -= 1

		print self.seededlist
		self.checkRound(**kwargs)

	def endTourney(self, **kwargs):
		winner = self.seededlist[0]
		name = winner['name']
		clinum = winner['clinum']
		wins = winner['totalwins']
		kwargs['Broadcast'].broadcast("ServerChat ^cThis tournament is over! The winner is %s with a total of %s wins." % (name, wins))
		kwargs['Broadcast'].broadcast("set _winnerind #GetIndexFromClientNum(%s)" % (clinum))
		self.tourneylist = {'totalplayers' : 0, 'players' : []}
		self.seededlist = []
		self.STARTED = 0
		self.ORGANIZER = -1
		self.RECRUIT = False
		self.TOURNEYROUND = 0
		for each in self.playerlist:
			each['register'] = 0
		
		kwargs['Broadcast'].broadcast("ExecScript GlobalClear; ClientExecScript -1 ClientClear; ExecScript GlobalSync")

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
		#remove a player when they have been defeated
		for each in self.seededlist:
			if each['clinum'] == clinum:
				self.seededlist.remove(each)

		

				
