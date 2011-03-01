# -*- coding: utf-8 -*-

import os
import re
import math
import time
import ConfigParser
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler

#This plugin was written by Old55 and he takes full responsibility for the junk below.
#He does not know python so the goal was to make something functional, not something
#efficient or pretty.


class norunes(ConsolePlugin):

	ms = None
	
	def onPluginLoad(self, config, **kwargs):
		self.ms = MasterServer ()

		ini = ConfigParser.ConfigParser()
		ini.read(config)
		#for (name, value) in config.items('balancer'):
		#	if (name == "level"):
		#		self._level = int(value)

		#	if (name == "sf"):
		#		self._sf = int(value)
		
		
		pass
	
	def onItemTransaction(self, *args, **kwargs):
		#adjust 'value' in playerlist to reflect what the player has bought or sold
		cli = args[0]
		trans = args[1]
		newitem = args[2]
		slot = args[3]

		if trans == 'BOUGHT' and newitem == 'PERSISTANT':
			kwargs['Broadcast'].broadcast("set _index #GetIndexFromClientNum(%s)#; TakeItem #_index# %s; set _index 0" % (cli, slot))
	
	def onPhaseChange(self, *args, **kwargs):
		kwargs['Broadcast'].put("RegisterGlobalScript -1 \"set _client #GetScriptParam(clientid)#; set _none \"\"; set _item #GetScriptParam(itemname)#; if #StringEquals(|#_item|#,|#_none|#)# set _item PERSISTANT; set _slot #GetScriptParam(slot)#; echo ITEM: Client #_client# BOUGHT #_item# #_slot#; echo\" buyitem")
		
