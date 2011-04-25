# -*- coding: utf-8 -*-
#22/4/11 - Send stats to both S2G and Salvage servers
import re
import ConfigParser
import thread
import glob
import os
import shutil
from StatsServers import StatsServers
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler

class sendstats(ConsolePlugin):
	base = None
	sent = None
	
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
			try:
				self.ss.s2gstats(statstring)
				self.ss.salvagestats(statstring)
			except:
				print 'upload failed. no stats sent'				
				return

			print 'Sent stat string'
			shutil.move(infile,sentdir)
			infile.close()


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
			
