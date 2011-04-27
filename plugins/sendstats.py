# -*- coding: utf-8 -*-
#22/4/11 - Send stats to both S2G and Salvage servers
import re
import ConfigParser
import thread
import glob
import os
import shutil
import urllib
from StatsServers import StatsServers
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler

class sendstats(ConsolePlugin):
	base = None
	sent = None
	playerlist = []

	def onPluginLoad(self, config):
		
		ini = ConfigParser.ConfigParser()
		ini.read(config)

		for (name, value) in ini.items('paths'):
			if (name == "base"):
				self.base = value
			if (name == "sent"):
				self.sent = value


	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
	
		#Everytime we start a game, start a new thread to send all the stats to eaxs' script, and replays to stony
		if (phase == 6):
						 
			uploadthread = thread.start_new_thread(self.uploadstats, ())
			replaythread = thread.start_new_thread(self.uploadreplay, ())

	def uploadstats(self):
		print 'starting uploadstats'
		self.ss = StatsServers ()
		home  = os.environ['HOME']
		path = 	os.path.join(home, self.base)
		sentdir = os.path.join(home, self.sent)
		
		for infile in glob.glob( os.path.join(home, self.base,'*.stats') ):
			print "Sending stat file: " + infile
			statstring = open(infile, 'r').read()
			decoded = urllib.quote(statstring)
			stats = ("stats=%s" % (decoded))

			try:
				self.ss.s2gstats(statstring)
				self.ss.salvagestats(stats)
			except:
				print 'upload failed. no stats sent'				
				return

			print 'Sent stat string'
			shutil.move(infile,sentdir)
			


	def uploadreplay(self):
		print 'starting uploadreplay'
		self.ss = StatsServers ()
		home  = os.environ['HOME']
		path = 	os.path.join(home, self.base)
		sentdir = os.path.join(home, self.sent)
		
		for infile in glob.glob( os.path.join(home, self.base,'*.s2r') ):
			print "Sending replay file: " + infile
			
			try:
				self.ss.sendreplay(infile)
				
			except:
				print 'upload failed. replay not sent'				
				return

			print 'Sent replay'
			shutil.move(infile,sentdir)

	def getPlayerByClientNum(self, cli):

		for client in self.playerlist:
			if (client['clinum'] == cli):
				return client

	def onConnect(self, *args, **kwargs):
		
		id = args[0]
		
		self.playerlist.append ({'clinum' : id, 'acctid' : 0,'name' : 'X'})

	def onSetName(self, *args, **kwargs):
				
		cli = args[0]
		playername = args[1]

		client = self.getPlayerByClientNum(cli)
		client ['name'] = playername

	def onAccountId(self, *args, **kwargs):
		self.ss = StatsServers ()
		cli = args[0]
		id = args[1]
		client = self.getPlayerByClientNum(cli)
		client ['acctid'] = int(id)
		name = client ['name']
		#print client
		playerinfo = ("sync_user=1&username=%s&acc=%s" % (name, id))
		#print playerinfo	
		self.ss.salvagestats(playerinfo)			
