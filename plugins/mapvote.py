# -*- coding: utf-8 -*-
# 2/28/11 - Turn off getlevels since it isn't working well in some cases. Add lifetime SF for 0 sf old players
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


class mapvote(ConsolePlugin):
	VERSION = "0.0.1"
	ms = None
	PHASE = 0
	playerlist = []
	maplist = []
	votelist = {'votes' : 0, 'playervotes' : []}
	TOTALPLAYERS = 0
	VOTEPERCENT = 40
	MINPLAYERS = 0
	NEWMAP = None
	MAPVOTE = True
	def onPluginLoad(self, config):
		self.ms = MasterServer ()

		ini = ConfigParser.ConfigParser()
		ini.read(config)
		#for (name, value) in config.items('mapvote'):
		#	if (name == "level"):
		#		self._level = int(value)

		#	if (name == "sf"):
		#		self._sf = int(value)
		for (name, value) in ini.items('maps'):
			self.maplist.append({'name' : name, 'status' : value})

		for (name, value) in ini.items('var'):
			if (name == "votepercent"):
				self.VOTEPERCENT = value
			if (name == "minplayers"):
				self.MINPLAYERS = value

		print self.MINPLAYERS, self.VOTEPERCENT
		pass

	def onStartServer(self, *args, **kwargs):
		
		print 'serverstarted'


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
				
		self.playerlist.append ({'clinum' : id, 'acctid' : 0, 'name' : 'X', 'active' : 0})
		


	def onSetName(self, *args, **kwargs):
		mapnames = []
		for each in self.maplist:
			mapnames.append(each['name'])
			
		mapnames = ', '.join(mapnames)
		
		mapmessage = "^cThis server is currently equipped with the ability to vote for a map change. Before a game has started you can send the message to ^rALL ^cchat: ^ynextmap mapname"
		mapmessage2 = "^cThis will register your vote for that map."
		mapmessage3 = ("^cCurrent valid maps are: ^y%s" % (mapnames))	
		cli = args[0]
		playername = args[1]
		client = self.getPlayerByClientNum(cli)
		client ['name'] = playername
		kwargs['Broadcast'].broadcast("SendMessage %s %s" % (client['clinum'], mapmessage))
		kwargs['Broadcast'].broadcast("SendMessage %s %s" % (client['clinum'], mapmessage2))
		kwargs['Broadcast'].broadcast("SendMessage %s %s" % (client['clinum'], mapmessage3))

	def onAccountId(self, *args, **kwargs):
		self.TOTALPLAYERS += 1
		cli = args[0]
		id = args[1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		
		client = self.getPlayerByClientNum(cli)

		client ['acctid'] = int(id)
		client ['active'] = 1
		
		

	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		client = self.getPlayerByClientNum(cli)

		for each in self.playerlist:
			if cli == each['clinum']:
				each['active'] = 0

		#if a player has voted and disconnects, remove their vote
		for each in self.votelist['playervotes']:
			if each['player'] == client['name']:
				self.votelist['playervotes'].remove(each)
				self.votelist['votes'] -= 1

		self.TOTALPLAYERS -= 1

		

	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		self.PHASE = phase
	
		if (phase == 7):
			self.onGameEnd(**kwargs)
		
		if (phase == 6):
			self.clearMapVotes(*args, **kwargs)

		if (phase == 5):
			self.clearMapVotes(*args, **kwargs)

	def onNewGame(self, *args, **kwargs):
		
		if (self.PICKING == 1):
			print 'team picking has begun, do not clear team player lists'
			kwargs['Broadcast'].broadcast("echo team picking has begun, do not clear team player lists!")
			
			self.PICKING = 0
			return

	def voteCheck(self, *args, **kwargs):
		tie = False
		totalplayers = self.TOTALPLAYERS 
		totalvotes = self.votelist['votes']
		minplayers = int(self.MINPLAYERS)
		threshold = int(self.VOTEPERCENT)
		votepercent = int(totalvotes/totalplayers) * 100
		#At least this many players must be present to even trigger a map selection
		if totalplayers < minplayers:
			print totalplayers
			print 'minplayer abort'
			return
		#This percentage of the total number of players must vote to trigger a map selection
		if votepercent < threshold:
			print votepercent
			print 'percent abort'
			return

		#determine which map has the most votes
		d = {}
		for votes in self.votelist['playervotes']:
			maps = votes['mapvote']
			d.setdefault(maps,0)
			d[maps] += 1

		items = [(v, k) for k, v in d.items()]
      		items.sort()
      		items.reverse()           
       		size = len(items)
		if size > 1:
			if items[0][0] == items[1][0]:
				print 'we have a tie'
				tie = True	
		if tie:
			kwargs['Broadcast'].broadcast("Serverchat ^cThere is a tie between ^r%s ^cand ^r%s. ^cIf you would like to change your vote you may do so." % (items[0][1], items[1][1]))
			return
		
		#We have a map winner
		newmap = items[0][1]			
		self.ChangeMap(newmap, **kwargs)

	def ChangeMap(self, newmap, **kwargs):

		status = 'official'

		for each in self.maplist:
			if each['name'] == newmap:
				status = each['status']
		if status == 'unofficial':
			kwargs['Broadcast'].broadcast("set svr_sendStats false; set svr_official false ")

		kwargs['Broadcast'].broadcast("changeworld %s" % (newmap))
		self.clearMapVotes(*args, **kwargs)

	def onMessage(self, *args, **kwargs):
		voted = False
		votemap = None
		#ignore anything that isn't sent to ALL chat
		if args[0] != "ALL":
			return
		#if the game has started, or we are in end phase, ignore
		if self.PHASE == 5 or self.PHASE == 7:
			return

		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
			
		mapvote = re.match("nextmap (\S+)", message, flags=re.IGNORECASE)
		formap = mapvote.group(1)
		
		if not mapvote:
			return
		
		if mapvote:
			
			voted = self.CheckVoted(client)
			
			for maps in self.maplist:
				if formap == maps['name']:
					
					votemap = formap

			if votemap == None:
				#Map name is invalid, tell them they got it wrong
				kwargs['Broadcast'].broadcast("SendMessage %s ^cMap name not recognized." % (client['clinum']))
				return
		
		#player has already voted, just change their map selection
		if voted:
			for each in self.votelist['playervotes']:
				if each['player'] == client['name']:
					each['mapvote'] = votemap
					kwargs['Broadcast'].broadcast("SendMessage %s ^cYou have switched your vote to ^r%s." % (client['clinum'], votemap))
					self.reportVotes(**kwargs)
					self.voteCheck(**kwargs)
					return
		#player has not yet voted, add to the total number of votes and add their selection to the list
		self.votelist['votes'] += 1
		self.votelist['playervotes'].append({'player' : client['name'], 'mapvote' : votemap})
		kwargs['Broadcast'].broadcast("SendMessage %s ^cYou have voted for ^r%s." % (client['clinum'], votemap))
		self.reportVotes(**kwargs)
		#check to see if all the voting critera have been met
		self.voteCheck(**kwargs)

	def CheckVoted(self, client, **kwargs):
		
		for each in self.votelist['playervotes']:
			if each['player'] == client['name']:
				return True			
		
	
	def clearMapVotes(self, *args, **kwargs):

		self.votelist = {'votes' : 0, 'playervotes' : []}	
		self.TOTALPLAYERS = 0
	def reportVotes(self, *args, **kwargs):
			
		d = {}
		for votes in self.votelist['playervotes']:
			maps = votes['mapvote']
			d.setdefault(maps,0)
			d[maps] += 1

		items = [(v, k) for k, v in d.items()]
      		items.sort()
      		items.reverse()

		for each in items:
			kwargs['Broadcast'].broadcast("Serverchat ^cVotes for ^r%s: ^c%s" % (each[1], each[0]))	

	def onGameEnd(self, *args, **kwargs):

		kwargs['Broadcast'].broadcast("set svr_sendStats true; set svr_official true")
