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


class balancer(ConsolePlugin):
	VERSION = "1.0.5"
	ms = None
	TIME = 0
	THRESHOLD = 6
	DIFFERENCE = -1
	GAMESTARTED = 0
	STARTSTAMP = 0
	DENY = 0
	OPTION = 0
	PICKING = 0
	CHAT_INTERVAL = 10
	CHAT_STAMP = 0
	PHASE = 0
	TOTAL1 = 0
	TOTAL2 = 0
	STAMPS = 0
	reason = "Your Skill Factor is 0. Please play some matches on official beginner servers to get some stats before you join this server."
	playerlist = []
	itemlist = []
	balancereport = []
	teamOne = {'size' : 0, 'avgBF' : -1, 'combinedBF' : 0, 'players' : []}
	teamTwo = {'size' : 0, 'avgBF' : -1, 'combinedBF' : 0, 'players' : []}
	game = {'size' : 0, 'avgBF' : -1}
	switchlist = []
	followlist = []

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
		
		self.TIME = 0
		self.THRESHOLD = 6
		self.DIFFERENCE = -1
		self.GAMESTARTED = 0
		self.STARTSTAMP = 0
		self.DENY = 0
		self.OPTION = 0
		self.PICKING = 0
		self.CHAT_INTERVAL = 10
		self.CHAT_STAMP = 0
		self.PHASE = 0
		self.TOTAL1 = 0
		self.TOTAL2 = 0
		self.STAMPS = 0
		self.playerlist = []
		self.itemlist = []
		self.balancereport = []
		self.teamOne = {'size' : 0, 'avgBF' : -1, 'combinedBF' : 0, 'players' : []}
		self.teamTwo = {'size' : 0, 'avgBF' : -1, 'combinedBF' : 0, 'players' : []}
		self.game = {'size' : 0, 'avgBF' : -1}
		self.switchlist = []
		self.followlist = []


	def getPlayerByClientNum(self, cli):

		for client in self.playerlist:
			if (client['clinum'] == cli):
				return client

	def getPlayerByName(self, name):

		for client in self.playerlist:
			if (client['name'].lower() == name.lower()):
				return client

	def onRefresh(self, *args, **kwargs):
		
		del self.teamOne ['players'][:]
		del self.teamTwo ['players'][:]
		self.teamOne ['size'] = 0
		self.teamTwo ['size'] = 0
		
		
		for client in self.playerlist:
			if (client['active'] == 1):
				kwargs['Broadcast'].broadcast("set _idx #GetIndexFromClientNum(%s)#; set _team #GetTeam(|#_idx|#)#; echo CLIENT %s is on TEAM #_team#" % (client['clinum'], client['clinum']))
				

	def onRefreshTeams(self, *args, **kwargs):
		
		clinum = args[0]
		team = int(args[1])
		
		if (team > 0):
			client = self.getPlayerByClientNum(clinum)
			teamlists = self.GetTeamLists(client, team)
			fromteam = teamlists ['fromteam']
			
			self.addTeamMember(client, fromteam, team, **kwargs)
			
			return
		

		

	def onConnect(self, *args, **kwargs):
		
		id = args[0]
		
		for client in self.playerlist:
			if (client['clinum'] == id):
				#added 10/12. If a player DCs and reconnects, they are auto-joined to their old team
				#but there is no team join message. This automatically adds them back to the balancer team list.
				print 'already have entry with that clientnum!'
				team = int(client['team'])
				
				if (team > 0):
					teamlists = self.GetTeamLists(client, team)
					toteam = teamlists ['toteam']
					fromteam = teamlists ['fromteam']
					self.addTeamMember(client, fromteam, team, **kwargs)
					client ['active'] = 1
					return
				return
		self.playerlist.append ({'clinum' : id, 'acctid' : 0, 'level' : 0, 'sf' : 0, 'bf' : 0, 'lf' : 0, 'name' : 'X', 'team' : 0, 'moved' : 0, 'index' : 0, 'exp' : 2, 'value' : 150, 'prevent' : 0, 'active' : 0, 'gamelevel' : 1})
		

	def onSetName(self, *args, **kwargs):

				
		cli = args[0]
		playername = args[1]
		

		client = self.getPlayerByClientNum(cli)

		client ['name'] = playername
		


	def onAccountId(self, *args, **kwargs):

		doKick = False

		cli = args[0]
		id = args[1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		
		level = int(stats['level'])
		sf = int(stats['sf'])
		lf = int(stats['lf'])
		exp = int(stats['exp'])
		time = int(stats['secs'])
		if sf == 0 and exp > 500:
			time = time/60
			sf = int(exp/time)
		client = self.getPlayerByClientNum(cli)

		client ['acctid'] = int(id)
		client ['level'] = level
		client ['sf'] = sf
		client ['lf'] = lf
		client ['exp'] = exp
		client ['active'] = 1
		if sf == 0:
			doKick = True
			
		if doKick:
			kwargs['Broadcast'].broadcast("kick %s \"%s\"" % (cli, self.reason))

		self.retrieveLevels(cli, **kwargs)

	def checkForSpectator (self, cli):
		player = self.getPlayerByClientNum(cli)

		if (player['team'] > 0):
			
			return cli
		else:
			return -1
	
	def getTeamMember (self, item, cli, fromteam):
		
		indice = -1
		
		for player in fromteam['players']:
			
			indice += 1
							
			if (player['clinum'] == cli):
				
				return indice
			
					
	def getPlayerIndex (self, cli):
		
		indice = -1
		for player in self.playlist:
			indice += 1
							
			if (player['clinum'] == cli):
				return indice
			
			
	def removeTeamMember (self, client, fromteam, team, **kwargs):
		print 'Removing player....'
		client ['team'] = team
		cli = client ['clinum']
		item = 'clinum'
		PLAYER_INDICE = self.getTeamMember(item, cli, fromteam)
		fromteam ['combinedBF'] -= fromteam['players'][PLAYER_INDICE]['bf']
		del fromteam['players'][PLAYER_INDICE]
		
		self.getGameInfo(**kwargs)

	def addTeamMember (self, client, toteam, team, **kwargs):
		
		print 'Adding player....'	
		cli = client['clinum']
		client ['active'] = 1
		NAME = client['name']
		level = client['level']
		SF = client['sf']
		BF = SF + level + (client ['gamelevel'] * 4)
		LF = client['lf'] + 10 + level
		moved = client['moved']
		client ['team'] = team
		client ['bf'] = BF + (client ['gamelevel'] * 4)
		toteam ['players'].append ({'clinum' : cli, 'name' : NAME, 'sf' : SF,  'lf' : LF, 'level' : level, 'moved' : moved, 'bf' : BF})
		
		self.getGameInfo(**kwargs)

	def GetTeamLists (self, client, team):

		currentteam = client ['team']
		
		L = {'toteam' : '0', 'fromteam' : '0'}

		if (int(currentteam) == 1):
			L ['fromteam'] = self.teamOne
			L ['toteam'] = self.teamTwo
			return L
		if (int(currentteam) == 2):
			L ['fromteam'] = self.teamTwo
			L ['toteam'] = self.teamOne
			return L

		if (int(team) == 1):
			L ['toteam'] = self.teamOne
			
		if (int(team) == 2):
			L ['toteam'] = self.teamTwo
			
				
		return L
		#don't think I need this but I am leaving it in
		del L [0]

	def onTeamChange (self, *args, **kwargs):
		
		spec = -1
		team = int(args[1])
		cli = args[0]
		self.retrieveLevels(cli, **kwargs)
		client = self.getPlayerByClientNum(cli)
		currentteam = client ['team']
		prevented = int(client ['prevent'])
		teamlists = self.GetTeamLists(client, team)
		toteam = teamlists ['toteam']
		fromteam = teamlists ['fromteam']

		if (self.DENY == 1):
			self.DIFFERENCE = abs(self.evaluateBalance())
			diff = self.DIFFERENCE

		#check to see if the player is on a team and going to spectator. spec = -1 unless the player is already on a team
		if (int(team) == 0):
			spec = self.checkForSpectator(cli)
		#need to have this to avoid having players added multiple times as I have seen happen
		if (spec == -1) and (int(currentteam) == int(team)):
			
			return
		#if the player is switching teams, add them to the new team and remove from the old			
		if (spec == -1) and (int(currentteam) > 0):
			
			self.addTeamMember(client, toteam, team, **kwargs)
			self.removeTeamMember(client, fromteam, team, **kwargs)
		#if the player hasn't joined a team yet, go ahead and add them to the team	
		elif (spec == -1):
			self.addTeamMember(client, toteam, team, **kwargs)
			self.getGameInfo(**kwargs)
			#Players are prevented from joining in the deny phase if they will cause greater than a 10% stack
			#this applies to both even and uneven games. The player is forced back to team 0.
			if (self.DENY == 1):
				self.DIFFERENCE = abs(self.evaluateBalance())
				if (self.DIFFERENCE > 10) and (self.DIFFERENCE > diff):
					action = 'PREVENT'
					self.retrieveIndex(client, action, **kwargs)
					return
				#There may be an issue if the player is forced back to team 0 that they can't join a team
				#even if conditions are met. This just forcibly puts the player on the team they are are trying to join
				#provided the above critera is not true.
				if (prevented == 1):
					action = 'ALLOW'
					self.retrieveIndex(client, action, **kwargs)
					
		#if the player is going to spec, just remove them from the team
		if (spec > -1):
			self.removeTeamMember(client, fromteam, team, **kwargs)
						
		self.OPTION = 0
						

	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		client = self.getPlayerByClientNum(cli)

		team = client ['team']

		if (int(team) > 0):

			teamlist = self.GetTeamLists(client, team)
			fromteam = teamlist ['fromteam']
			self.removeTeamMember(client, fromteam, team, **kwargs)
			
		#self.sendGameInfo(**kwargs)
		client ['active'] = 0

	def onCommResign(self, *args, **kwargs):
		name = args[0]
		
		client = self.getPlayerByName(name)
		team = client['team']
		cli = client['clinum']
		
		teamlist = self.GetTeamLists(client, team)
		fromteam = teamlist ['fromteam']
		item = 'clinum'
		PLAYER_INDICE = self.getTeamMember(item, cli, fromteam)
		
		#fromteam['players'][PLAYER_INDICE]['bf'] = client ['sf']
		fromteam['players'][PLAYER_INDICE]['bf'] = int(client['sf'] + client['level'] + (client['gamelevel']*4))
		fromteam['players'][PLAYER_INDICE]['moved'] = 0
		
		client ['moved'] = 0	
		
		

	def onUnitChange(self, *args, **kwargs):
		if args[1] != "Player_Commander":
			return

		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		team = client['team']
		teamlist = self.GetTeamLists(client, team)
		fromteam = teamlist ['fromteam']
		item = 'clinum'
		PLAYER_INDICE = self.getTeamMember(item, cli, fromteam)
		
		#fromteam['players'][PLAYER_INDICE]['bf'] = client ['lf']
		fromteam['players'][PLAYER_INDICE]['bf'] = fromteam['players'][PLAYER_INDICE]['lf']
		fromteam['players'][PLAYER_INDICE]['moved'] = 1
		#set moved to 1 to prevent the player from being auto-swapped as commander
		client['moved'] = 1
		
		

	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		self.PHASE = phase
	
		if (phase == 7):
			self.onGameEnd(**kwargs)
		if (phase == 5):
			self.onGameStart(*args, **kwargs)
			self.PICKING = 0
		if (phase == 3):
			self.PICKING = 1
		if (phase == 6):
			self.onNewGame(*args, **kwargs)
			
		
	def onGameEnd(self, *args, **kwargs):
		
		avg1 = int(self.TOTAL1/self.STAMPS)
		avg2 = int(self.TOTAL2/self.STAMPS)
		print avg1, avg2, self.STAMPS
		kwargs['Broadcast'].broadcast("Serverchat ^cHow stacked was this game from start to finish? Humans had an average combined BF of ^r%s^c, Beasts had an average combined BF of ^r%s ^cfrom a total of ^y%s ^ctime points." % (avg1, avg2, self.STAMPS))
		#clear out the team dictionary info and globals when the map is reloaded
		del self.teamOne ['players'][:]
		del self.teamTwo ['players'][:]
		for player in self.playerlist:
			player ['active'] = 0
			player ['team'] = 0
			player ['gamelevel'] = 1
			player ['bf'] = int(player ['sf'] + player ['level'])
			player ['value'] = 150
		self.teamOne ['size'] = 0
		self.teamOne ['avgBF'] = -1
		self.teamOne ['combinedBF'] = 0
		self.teamTwo ['size'] = 0
		self.teamTwo ['avgBF'] = -1
		self.teamTwo ['combinedBF'] = 0
		self.GAMESTARTED = 0
		self.STARTSTAMP = 0
		self.DENY = 0
		self.OPTION = 0
		self.DIFFERENCE = -1
		self.PICKING = 0
		self.balancereport = []
		#self.playerlist = []		
		self.TOTAL1 = 0
		self.TOTAL2 = 0
		self.STAMPS = 0
	def onNewGame(self, *args, **kwargs):
		
		if (self.PICKING == 1):
			print 'team picking has begun, do not clear team player lists'
			kwargs['Broadcast'].broadcast("echo team picking has begun, do not clear team player lists!")
			
			self.PICKING = 0
			return

		
		#clear out the team dictionary info and globals when the map is reloaded
		del self.teamOne ['players'][:]
		del self.teamTwo ['players'][:]
		for player in self.playerlist:
			player ['active'] = 0
			player ['team'] = 0
			player ['gamelevel'] = 1
			player ['bf'] = int(player ['sf'] + player ['level'])
			player ['value'] = 150
		self.teamOne ['size'] = 0
		self.teamOne ['avgBF'] = -1
		self.teamOne ['combinedBF'] = 0
		self.teamTwo ['size'] = 0
		self.teamTwo ['avgBF'] = -1
		self.teamTwo ['combinedBF'] = 0
		self.GAMESTARTED = 0
		self.STARTSTAMP = 0
		self.DENY = 0
		self.OPTION = 0
		self.DIFFERENCE = -1
					

		self.RegisterScripts(**kwargs)

	def RegisterScripts(self, **kwargs):
		#any extra scripts that need to go in can be done here
		#these are for identifying bought and sold items
		kwargs['Broadcast'].put("RegisterGlobalScript -1 \"set _client #GetScriptParam(clientid)#; set _item #GetScriptParam(itemname)#; echo ITEM: Client #_client# SOLD #_item#; echo\" sellitem")
		kwargs['Broadcast'].put("RegisterGlobalScript -1 \"set _client #GetScriptParam(clientid)#; set _item #GetScriptParam(itemname)#; echo ITEM: Client #_client# BOUGHT #_item#; echo\" buyitem")
		#this makes sure we get an update every thirty seconds.
		kwargs['Broadcast'].put("set sv_statusNotifyTime 30000")
		kwargs['Broadcast'].broadcast()

	def ItemList(self, *args, **kwargs):
		#The item list to get gold values. I had hoped to make this more dynamic, but the server won't return 'Consumable_Advanced_Sights' so it is difficult to get the value
		#directly from game_settings.cfg. Modification to remove appends from winex, 10/12.
		self.itemlist = {
			'Advanced Sights' : 700,
			'Ammo Pack' : 500,
			'Ammo Satchel' : 200,
			'Chainmail' : 300,
			'Gust of Wind' : 450,
			'Magic Amplifier' : 700,
			'Brain of Maliken' : 750,
			'Heart of Maliken' : 950,
			'Lungs of Maliken' : 800,
			'Mana Crystal' : 500,
			'Mana Stone' : 200,
			'Platemail' : 650,
			'Power Absorption' : 350,
			'Shield of Wisdom' : 650,
			'Stone Hide' : 650,
			'Tough Skin' : 300,
			'Trinket of Restoration' : 575,
		}


	def onItemTransaction(self, *args, **kwargs):
		#adjust 'value' in playerlist to reflect what the player has bought or sold
		cli = args[0]
		trans = args[1]
		newitem = args[2]
		client = self.getPlayerByClientNum(cli)

		try:
			value = self.itemlist[newitem]
		except:
			return

		if (trans == 'BOUGHT'):
			client['value'] += value
		elif (trans == 'SOLD'):
			client['value'] -= value


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
		if (action == 'LEVEL'):
			self.level(clinum, index, **kwargs)

	def runBalancer (self, **kwargs):
		#determines if it is even or uneven balancer
		

		diff = self.teamOne['size'] - self.teamTwo['size']
		print diff
		if (diff == 0):
			self.EvenTeamBalancer(**kwargs)
		#uneven balancer if there is a difference between 1-3. if it more than that, it would be best to restart, but that has not been implemented
		elif (abs(diff) > 0 and abs(diff) < 4):
			
			self.UnEvenTeamBalancer(**kwargs)
			
		else:
			return

	def onGameStart (self, *args, **kwargs):
		
		self.ItemList()
		self.STARTSTAMP = args[1]
		self.GAMESTARTED = 1
		kwargs['Broadcast'].broadcast("echo GAMESTARTED")

		self.sendGameInfo(**kwargs)
		
		
		kwargs['Broadcast'].put("ServerChat ^cIf necessary, the teams will be auto-balanced at 1, 3, and 6 minutes of game time.")
		kwargs['Broadcast'].put("ServerChat ^cAfter 6 minutes, joining will be limited to players that do not generate imbalance.")
		kwargs['Broadcast'].put("ServerChat ^cAt 5 minute increments starting at minute 10, the server will check for imbalance and notify players that they will be switched in one minute unless they reject the move.")
		kwargs['Broadcast'].put("ServerChat ^cSelected players may send the message 'reject' to ^bALL ^cchat to prevent the change.")
		kwargs['Broadcast'].broadcast()
		self.RegisterScripts(**kwargs)
		self.startFollow(**kwargs)

	
	def onServerStatus(self, *args, **kwargs):
		CURRENTSTAMP = int(args[1])
		self.TIME = int(CURRENTSTAMP) - int(self.STARTSTAMP)
		#self.getTeamLevels(**kwargs)
		kwargs['Broadcast'].broadcast("set _team1num #GetNumClients(1)#; set _team2num #GetNumClients(2)#; echo SERVER-SIDE client count, Team 1 #_team1num#, Team 2 #_team2num#")
		
		if (self.GAMESTARTED == 1):
			self.TOTAL1 += self.teamOne['combinedBF']
			self.TOTAL2 += self.teamTwo['combinedBF']
			self.STAMPS += 1

	def evaluateBalance(self, BF1=0.0, BF2=0.0, moving=False, **kwargs):
		large = self.getLargeTeam()
		small = self.getSmallTeam()
		largebf = float(large ['combinedBF'])
		smallbf = float(small ['combinedBF'])
		totalbf = largebf + smallbf
		largeshare = (largebf - BF1 + BF2) / totalbf
		smallshare = (smallbf + BF1 - BF2) / totalbf
		largesize = float(large ['size'])
		smallsize = float(small ['size'])
		totalsize = largesize + smallsize
		if moving:
			largesize = float(large ['size']) - 1.0
			smallsize = float(small ['size']) + 1.0
		
		sizediff = largesize / totalsize
		largepercent = largeshare + sizediff
		return (largepercent - 1) * 100
 
	def getClosestPersonToTarget (self, team, **kwargs):
		
		lowest = -1
		pick = None
		
		
		for player1 in team ['players']:

			if (player1['moved'] == 1):
				continue

			
			ltarget = abs(self.evaluateBalance (float(player1 ['bf']), 0.0, True))
			print ltarget
			if (lowest < 0):
				lowest = ltarget
				# wouldn't work if the first player was the one to pick, so had to do this here
				pick = player1
				continue
			
			if (lowest < ltarget):
				continue
			
			lowest = ltarget
			pick = player1
		
		print pick

		if (pick == None):
			kwargs['Broadcast'].broadcast("echo BALANCER: UNEVEN balancer was not happy for some reason I can't figure out")
			return

				
		kwargs['Broadcast'].broadcast("echo BALANCER: UNEVEN balancer selections: Client %s with bf %s for a starting BF stacking of %s to %s" % (pick['clinum'], pick['bf'], self.DIFFERENCE, lowest))
		#if the selected option doesn't actually improve anything, terminate
		if (lowest > self.DIFFERENCE):
			kwargs['Broadcast'].broadcast("echo BALANCER: unproductive UNEVEN balance")
			return

		if (self.OPTION == 0):	
			#get the player index and move them
			action = 'MOVE'
			self.retrieveIndex(pick, action, **kwargs)
			return
		
		if (self.OPTION == 1):
			self.switchlist.append ({'name' : pick ['name'], 'clinum' : pick ['clinum'], 'accept' : 0})
			print self.switchlist
			self.giveOption (**kwargs)
	
	
	def getClosestTwoToTarget (self, team1, team2, **kwargs):
		
		lowest = -1
		pick1 = None
		pick2 = None
		

		for player1 in team1 ['players']:
			if (player1['moved'] == 1):
				continue
			for player2 in team2 ['players']:

				if (player2['moved'] == 1):
					continue
				
				ltarget = abs(self.evaluateBalance (float(player1 ['bf']), float(player2 ['bf'])))
				
				if (lowest < 0):
					lowest = ltarget
					pick1 = player1
					pick2 = player2
					continue
			
				if (lowest < ltarget):
					continue
			
				lowest = ltarget
				pick1 = player1
				pick2 = player2

		
		print pick1, pick2


		kwargs['Broadcast'].broadcast("echo Balancer selections: Clients %s, %s with BF %s, %s." % (pick1['clinum'], pick2['clinum'], pick1['bf'], pick2['bf']))

		if (lowest >= self.DIFFERENCE):
			print 'unproductive balance. terminate'
			kwargs['Broadcast'].broadcast("echo unproductive EVEN balance")
			return

		if (self.OPTION == 0):
			action = 'MOVE'
			self.retrieveIndex(pick1, action, **kwargs)
			self.retrieveIndex(pick2, action, **kwargs)
			return

		if (self.OPTION == 1):
			self.switchlist.append ({'name' : pick1['name'], 'clinum' : pick1['clinum'], 'accept' : 0})
			self.switchlist.append ({'name' : pick2['name'], 'clinum' : pick2['clinum'], 'accept' : 0})
			print self.switchlist
			self.giveOption (**kwargs)
	
	def giveOption(self, **kwargs):
		
		index = -1
		playermessage = "^cYou have been selected to change teams to promote balance. You have one minute to REJECT this change by sending the message 'reject' to ^bALL ^cchat."
		for player in self.switchlist:
			index += 1
			kwargs['Broadcast'].put("SendMessage %s %s" % (player['clinum'], playermessage))

		if (index == 0):
			kwargs['Broadcast'].put("Serverchat ^cTeams are currently unbalanced. ^r%s ^chas been selected to improve balance. They will automatically switch teams in one minute unless they reject the move by sending the message 'reject' to ^bALL ^cchat, or another player joins." % (self.switchlist[0]['name']))
		else:
			kwargs['Broadcast'].put("Serverchat ^cTeams are currently unbalanced. ^r%s ^cand ^r%s ^chave been selected to improve balance. They will automatically switch teams in one minute unless one of them rejects the move by sending the message 'reject' to ^bALL ^cchat, or another player joins." % (self.switchlist[0]['name'], self.switchlist[1]['name']))
		kwargs['Broadcast'].broadcast()

	def onMessage(self, *args, **kwargs):
		
		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
		
		if (args[0] == "SQUAD") and (message == 'report balance'):
			self.getGameInfo()
			kwargs['Broadcast'].broadcast("SendMessage %s Balance Report: ^yTeam 1 combined: ^g%s (%s players, %s BF average), ^yTeam 2 combined: ^g%s (%s players, %s BF average). ^yStack percentage: ^r%s. ^yCurrent Phase: ^c%s. ^yCurrent time stamp: ^c%s. ^yBalancer active = ^r%s" % (client['clinum'], self.teamOne ['combinedBF'], self.teamOne ['size'], self.teamOne ['avgBF'], self.teamTwo ['combinedBF'], self.teamTwo ['size'], self.teamTwo ['avgBF'], round(self.evaluateBalance(), 1), self.PHASE, self.TIME, self.GAMESTARTED))
			for moves in self.balancereport:
				kwargs['Broadcast'].broadcast("SendMessage %s BALANCER: Balanced move for: %s at time %s" % (client['clinum'],moves ['name'], moves ['time']))

		if (args[0] == "SQUAD") and (message == 'report team one'):
			
			for player in self.teamOne ['players']:
				kwargs['Broadcast'].broadcast("SendMessage %s Team One Report: Player: ^c%s ^rBF: ^y%s" % (client['clinum'], player['name'], player['bf']))

		if (args[0] == "SQUAD") and (message == 'report team two'):
			
			for player in self.teamTwo ['players']:
				kwargs['Broadcast'].broadcast("SendMessage %s Team Two Report: Player: ^c%s ^rBF: ^y%s" % (client['clinum'], player['name'], player['bf']))

		if (args[0] == "SQUAD") and (message == 'report playerlist'):
			
			for active in self.playerlist: 
				if (active ['active'] == 1):
					kwargs['Broadcast'].broadcast("SendMessage %s Active Player List: Player: ^c%s ^rSF: ^y%s" % (client['clinum'], active['name'], active['sf']))
		if (args[0] == "SQUAD") and (message == 'report version'):
			
			kwargs['Broadcast'].broadcast("SendMessage %s Balancer version: ^y%s" % (client['clinum'], self.VERSION))

		#Beginnings of a following script for spectators
		followed = re.match("follow (\S+)", message, flags=re.IGNORECASE)
		stopfollow = re.match("stop follow", message, flags=re.IGNORECASE)
		if followed:
			followed_player = self.getPlayerByName(followed.group(1))
			if (followed_player ['team'] > 0) and (client ['team'] == 0):
				for each in self.followlist:
					if each ['follower'] == client['clinum']:
						each ['followed'] = followed_player['clinum']
						self.startFollow(**kwargs)
						return
					
				self.followlist.append ({'follower' : client['clinum'], 'followed' : followed_player['clinum']})
				
				self.startFollow(**kwargs)
				
			else:
				print 'conditions not met to follow'
				return
		if stopfollow:
			for followings in self.followlist:
				if followings ['follower'] == client ['clinum']:
					followings ['follower'] = -1
			
						
		if args[0] != "ALL":
			return

		
		
		if re.match(".*tell\s+(?:me\s+)?(?:the\s+)?(?:SFs?|balance)(?:\W.*)?$", message, flags=re.IGNORECASE):
			tm = time.time()
			if (tm - self.CHAT_STAMP) < self.CHAT_INTERVAL:
				return
			self.CHAT_STAMP = tm
			return self.sendGameInfo(**kwargs)

		if (self.OPTION == 1) and (message == 'reject'):
			for player in self.switchlist:
				if (player['name'] == name):
					kwargs['Broadcast'].broadcast("ServerChat ^r%s ^chas rejected a move to promote balance between the teams." % (name))
					del self.switchlist[:]

		

	def optionCheck(self, **kwargs):
		if (self.OPTION == 1):
			for player in self.switchlist:
				action = 'MOVE'
				self.retrieveIndex(player, action, **kwargs)
		del self.switchlist[:]

	def move(self, clinum, index, **kwargs):
		
		client = self.getPlayerByClientNum(clinum)
		
		client ['moved'] = 1
		name = client ['name']
		#only have to move players that are already on a team, and since they can only go to the other team we can use this
		if (int(client['team']) == 1):
			newteam = 2
		else:
			newteam = 1

		kwargs['Broadcast'].put("SetTeam %s %s" % (index, newteam))
		kwargs['Broadcast'].put("Serverchat ^r%s ^chas switched teams to promote balance." % (name))
		kwargs['Broadcast'].put("ResetAttributes %s" % (index))
		kwargs['Broadcast'].broadcast()

		self.balancereport.append ({'time' : self.TIME, 'client' : name})
		
		self.moveNotify(clinum, **kwargs)

	def prevent(self, clinum, index, **kwargs):
		client = self.getPlayerByClientNum(clinum)
		client ['prevent'] = 1
		newteam = 0
		kwargs['Broadcast'].broadcast("SetTeam %s %s" % (index, newteam))

		self.preventNotify(clinum, **kwargs)

	def allow(self, clinum, index, **kwargs):
		client = self.getPlayerByClientNum(clinum)
		team = client ['team']
		kwargs['Broadcast'].broadcast("SetTeam %s %s" % (index, team))
		client ['prevent'] = 0

	def level(self, clinum, index, **kwargs):
		client = self.getPlayerByClientNum(clinum)
		team = client ['team']		
		kwargs['Broadcast'].broadcast("set _plevel #GetLevel(%s)#; set team%s_level [team%s_level + _plevel]" % (index, team, team))
		

	def moveNotify(self, clinum, **kwargs):
		#this lets the player know the have been moved and compensates them for their purchased items. There is current no way to know
		#how much gold a player holds, though I think gold may actually transfer. Not 100% sure.
		client = self.getPlayerByClientNum(clinum)

		value = client ['value']

		kwargs['Broadcast'].put("SendMessage %s ^cYou have automatically switched teams to promote balance." % (clinum))
		kwargs['Broadcast'].put("SendMessage %s ^cYou have been compensated ^g%s ^cgold for your non-consumable items and your attributes have been reset." % (clinum, value))
		kwargs['Broadcast'].put("GiveGold %s %s" % (clinum, value))
		kwargs['Broadcast'].broadcast()

		client ['value'] = 0

	def preventNotify(self, clinum, **kwargs):
		kwargs['Broadcast'].broadcast("SendMessage %s ^cYou cannot join that team as it will create imbalance. Please wait for another player to join or leave." % (clinum))

	def getSmallTeam (self):
		#writing these all out explicitly because I was having trouble with them
		if (self.teamOne ['size'] < self.teamTwo ['size']):
			return self.teamOne
		if (self.teamTwo ['size'] < self.teamOne ['size']):
			return self.teamTwo
		if (self.teamTwo ['size'] == self.teamOne ['size']):
			return self.teamTwo

	def getLargeTeam (self):
		#writing these all out explicitly because I was having trouble with them
		if (self.teamOne ['size'] > self.teamTwo ['size']):
			return self.teamOne
		if (self.teamTwo ['size'] > self.teamOne ['size']):
			return self.teamTwo
		if (self.teamTwo ['size'] == self.teamOne ['size']):
			return self.teamOne

	def getHighTeam (self):
		if (self.teamOne ['avgBF'] > self.teamTwo ['avgBF']):
			return self.teamOne
		return self.teamTwo

	def getLowTeam (self):
		if (self.teamOne ['avgBF'] > self.teamTwo ['avgBF']):
			return self.teamTwo
		return self.teamOne

	def getTeamOne (self):
		return self.teamOne

	def getTeamTwo (self):
		return self.teamTwo

	def getTeamAvg (self, team):
		#this updates the info for a team
		
		team ['combinedBF'] = 0
		team ['size'] = 0
		for clients in team ['players']:
			team ['combinedBF'] += clients ['bf']
			team ['size'] += 1
		if (team ['size'] > 0):
			team ['avgBF'] = (team ['combinedBF'] / team ['size'])
		else:
			team ['avgBF'] = 0

	def getGameInfo (self, **kwargs):

		self.getTeamAvg (self.teamOne)
		self.getTeamAvg (self.teamTwo)
		self.game ['size'] = (self.teamOne ['size'] + self.teamTwo ['size'])
		self.game ['avgBF'] = ((self.teamOne ['avgBF'] +  self.teamTwo ['avgBF']) / 2)

		

	def sendGameInfo (self, **kwargs):
		self.getGameInfo(**kwargs)

		if (self.GAMESTARTED == 1):
			self.DIFFERENCE = abs(self.evaluateBalance())
			

		kwargs['Broadcast'].put("ServerChat ^cCurrent balance: ^yTeam 1 Avg. BF: ^g%s (%s players), ^yTeam 2 Avg. BF: ^g%s (%s players). Stack percentage: ^r%s" % (self.teamOne ['avgBF'], self.teamOne ['size'], self.teamTwo ['avgBF'], self.teamTwo ['size'], round(self.DIFFERENCE, 1) ))
		kwargs['Broadcast'].broadcast()


	def EvenTeamBalancer(self, **kwargs):
		self.getGameInfo(**kwargs)
		#added these to prevent any moves if there is an error in BF calculation that has sprung up on occasion
		for clients in self.teamOne['players']:
			if clients['bf'] > 1000:
				kwargs['Broadcast'].broadcast("echo refresh")
				return
		for clients in self.teamTwo['players']:
			if clients['bf'] > 1000:
				kwargs['Broadcast'].broadcast("echo refresh")
				return

		self.DIFFERENCE = abs(self.evaluateBalance())
		print(self.DIFFERENCE)

		if (self.DIFFERENCE > self.THRESHOLD):
			self.getClosestTwoToTarget (self.getLargeTeam (), self.getSmallTeam (),  **kwargs)
		else:
			
			kwargs['Broadcast'].broadcast("Serverchat ^cEven team balancer initiated but current balance percentage of ^y%s ^cdoes not meet the threshold of ^y%s" % (round(self.DIFFERENCE, 1), self.THRESHOLD))

	def UnEvenTeamBalancer(self, **kwargs):
		self.getGameInfo(**kwargs)
		#added these to prevent any moves if there is an error in BF calculation that has sprung up on occasion
		for clients in self.teamOne['players']:
			if clients['bf'] > 1000:
				kwargs['Broadcast'].broadcast("echo refresh")
				return
		for clients in self.teamTwo['players']:
			if clients['bf'] > 1000:
				kwargs['Broadcast'].broadcast("echo refresh")
				return		

		overcheck = self.evaluateBalance()
		self.DIFFERENCE = abs(self.evaluateBalance())
		#In this scenario, the larger team has a much lower BF, so do a player swap instead of a single move.
		if (overcheck < 0) and (self.DIFFERENCE > self.THRESHOLD):
			self.getClosestTwoToTarget (self.getLargeTeam (), self.getSmallTeam (), **kwargs)
			kwargs['Broadcast'].broadcast("echo BALANCER: ^cUneven team balancer with swap initiated")
			return
		#In this scenario, the larger team has greater BF, so do a single mvoe.
		if (overcheck > 0) and (self.DIFFERENCE > self.THRESHOLD):
			self.getClosestPersonToTarget (self.getLargeTeam (), **kwargs)
		else:
			print 'threshold not met'
			kwargs['Broadcast'].broadcast("Serverchat ^cUneven team balancer initiated, but current balance percentage of ^y%s ^cdoes not meet the threshold of ^y%s" % (round(self.DIFFERENCE, 1), self.THRESHOLD))

	def onTeamCheck(self, *args, **kwargs):
		if (self.TIME % (60 * 1000)) == 0:				
			self.sendGameInfo(**kwargs)
					
		if (self.teamOne ['size'] == int(args[0])) and (self.teamTwo ['size'] == int(args[1])):
			kwargs['Broadcast'].broadcast("echo BALANCER: Team 1 count is correct")
			kwargs['Broadcast'].broadcast("echo BALANCER: Team 2 count is correct")
		
			if (self.PHASE == 5):

				self.GAMESTARTED = 1
				
				if (self.TIME == (1 * 60 * 1000)):
					self.runBalancer (**kwargs)
				elif (self.TIME == (3 * 60 * 1000)):
					self.runBalancer (**kwargs)
				elif (self.TIME == (6 * 60 * 1000)):
					self.runBalancer (**kwargs)
				if (self.TIME >= (6 * 60 * 1000)):
					self.DENY = 1
					self.optionCheck(**kwargs)
					self.OPTION = 1
				
					if (self.TIME % (5 * 60 * 1000)) == 0:
						self.runBalancer (**kwargs)
			return
		else:
			#kwargs['Broadcast'].broadcast("Serverchat ^cBalancer is currently off until player counts can be verified.")
			kwargs['Broadcast'].broadcast("ListClients")
			kwargs['Broadcast'].broadcast("echo refresh")
			#this initiates turns balancer off and tries to refresh the teams to get the proper count
			self.GAMESTARTED = 0
			self.DENY = 0

	def retrieveLevels(self, cli, **kwargs):

		kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; set _plevel #GetLevel(|#_index|#)#;echo CLIENT %s is LEVEL #_plevel#; set _plevel 1" % (cli, cli))
		

	def getTeamLevels(self, **kwargs):
	
		if (self.GAMESTARTED == 1):
					
			for player1 in self.teamOne ['players']:
				self.retrieveLevels(player1 ['clinum'], **kwargs)
			for player2 in self.teamTwo ['players']:
				self.retrieveLevels(player2 ['clinum'], **kwargs)
				
			
	def onGetLevels(self, *args, **kwargs):
		clinum = args[0]
		level = int(args[1])
		client = self.getPlayerByClientNum(clinum)
		client ['gamelevel'] = level
		client ['bf'] = client ['sf'] + client ['level'] + (4*level)
		if (client ['team'] == 1):
			for player in self.teamOne ['players']:
				if client ['clinum'] == player ['clinum']:
					player ['bf'] = client ['bf']
		if (client ['team'] == 2):
			for player in self.teamTwo ['players']:
				if client ['clinum'] == player ['clinum']:
					player ['bf'] = client ['bf']

	def onListClients(self, *args, **kwargs):
		clinum = args[0]
		name = args[2]
		print 'making client active'
		client = self.getPlayerByName(name)
		client ['active'] = 1

	def onMapReset(self, *args, **kwargs):
		if (self.PHASE == 5):
			kwargs['Broadcast'].broadcast("prevphase")
			self.GAMESTARTED = 0
		else:
			return

	def startFollow(self, **kwargs):
		
		for followings in self.followlist:
			kwargs['Broadcast'].broadcast("set _follower #GetIndexFromClientNum(%s)#; set _followed #GetIndexFromClientNum(%s)#; set _x #GetPosX(|#_followed|#)#; set _y #GetPosY(|#_followed|#)#; set _z #GetPosZ(|#_followed|#)#; SetPosition #_follower# [_x + 200] [_y + 200] [_z + 200]" % (followings ['follower'], followings ['followed']))

		
		
			
