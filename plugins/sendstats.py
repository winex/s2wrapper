# -*- coding: utf-8 -*-
# 3.27.11 - Remove prev. phase command
import re
import ConfigParser
import thread
import glob
import os
import shutil
from MasterServer import MasterServer
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
	
		#Everytime we start a game, start a new thread to send all the stats to eaxs' script
		if (phase == 6):
						 
			uploadthread = thread.start_new_thread(self.uploadstats, ())
			
	def uploadstats(self):
		print 'starting uploadstats'
		self.ms = MasterServer ()
		home  = os.environ['HOME']
		print home
		path = 	os.path.join(home, self.base)
		print path
		for infile in glob.glob( os.path.join(home, self.base,'*.stats') ):
			print "Sending stat file: " + infile
			statstring = open(infile, 'r').read()
			self.ms.queryserver(statstring)
			print 'Sent stat string'
			shutil.move(os.path.join(infile),self.sent)

