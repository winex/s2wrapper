# -*- coding: utf-8 -*-
# Auto-update incorporation, yet another last test
import re
import ConfigParser
import threading
import random
import os
import PluginsManager
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler
from operator import itemgetter
import urllib2
import subprocess

class helper(ConsolePlugin):
	VERSION = "0.0.1"
	playerlist = []
	helperlist = []
	PHASE = 0
	CONFIG = None

	def onPluginLoad(self, config):
		
		self.ms = MasterServer ()
		self.CONFIG = config
		ini = ConfigParser.ConfigParser()
		ini.read(config)
		
		for (name, value) in ini.items('helpers'):
			self.helperlist.append({'name': name, 'level' : value})

		pass
		
	def reload_config(self):
		
        	self.helperlist = []
       		self.ipban = []
                ini = ConfigParser.ConfigParser()
                ini.read(self.CONFIG)

		for (name, value) in ini.items('helpers'):
			self.helperlist.append({'name': name, 'level' : value})

	def onStartServer(self, *args, **kwargs):
				
		self.playerlist = []

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
		
		for client in self.playerlist:
			if (client['clinum'] == id):
				return
		
		self.playerlist.append ({'clinum' : id,\
					 'acctid' : 0,\
					 'name' : 'X',\
					 'active' : False,\
					 'helper' : False,\
					 'level' : 0})
	
	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client ['active'] = False

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
		client['sf'] = sf
		client['level'] = level
		client['active'] = True
		client['helper'] = False

		if client['level'] <= 10:
			self.helperNotify(client, **kwargs)

		for each in self.helperlist:
			if client['name'].lower() == each['name']:
				client['helper'] = True

	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		self.PHASE = phase
		
		if (phase == 7):
			self.banlist = []	
			for each in self.playerlist:
				each['team'] = 0
				each['commander'] = False
					
		if (phase == 6):
			#fetch helper list and reload at the start of each game
			updatethread = threading.Thread(target=self.update, args=(), kwargs=kwargs)
			updatethread.start()	

	def update(self, **kwargs):
		
		response = urllib2.urlopen('http://188.40.92.72/helper.ini')
		helperlist = response.read()
			
		f = open(self.CONFIG, 'w')
		f.write(helperlist)
		f.close
		f.flush()
		os.fsync(f.fileno())
		self.reload_config()

	def helperNotify(self, client, **kwargs):
		
		activehelpers = []
		
		for player in self.playerlist:
			if player['helper'] and player['active']:
				activehelpers.append(player['name'])

		activestring = ', '.join(activehelpers)

		kwargs['Broadcast'].broadcast(\
		"SendMessage %s ^rATTENTION: ^cAs a new player it so good to get help from more experienced players. The following players on this server have \
		indicated their willingness to help newer players: ^y%s. ^cYou can contact them by using chat (^wCTRL+ENTER^c) and whispering them (^y/w playername^c with your message)."
			 % (client['clinum'], activestring))
			 
	def onListClients(self, *args, **kwargs):
		clinum = args[0]
		name = args[2]
		ip = args[1]
		
		
		client = self.getPlayerByName(name)
		if not client:
		#if a player is missing from the list this will put them as an active player
			acct = self.ms.getAccount(name)
			acctid = acct[name]
			self.onConnect(clinum, 0000, ip, 0000, **kwargs)
			self.onSetName(clinum, name, **kwargs)
			self.onAccountId(clinum, acctid, **kwargs)
