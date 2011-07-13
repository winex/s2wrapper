# -*- coding: utf-8 -*-

import os
import re
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler

#This plugin was written by Old55 and he takes full responsibility for the junk below.
#He does not know python so the goal was to make something functional, not something
#efficient or pretty.


class norunes(ConsolePlugin):

		
	def onPluginLoad(self, config, **kwargs):
		
		#ini = ConfigParser.ConfigParser()
		#ini.read(config)
		#for (name, value) in config.items('balancer'):
		#	if (name == "level"):
		#		self._level = int(value)

		#	if (name == "sf"):
		#		self._sf = int(value)
		
		
		pass
	
	def onPhaseChange(self, *args, **kwargs):
		kwargs['Broadcast'].broadcast(\
		"RegisterGlobalScript -1 \"set _client #GetScriptParam(clientid)#;\
		 set _buyindex #GetIndexFromClientNum(|#_client|#)#;\
		 set _none \"\"; set _item #GetScriptParam(itemname)#;\
		 if #StringEquals(|#_item|#,|#_none|#)# TakeItem #_buyindex# #GetScriptParam(slot)#;\
		 if #StringEquals(|#_item|#,|#_none|#)# SendMessage #GetScriptParam(clientid)# ^yYou cannot equip persistent items on this server; echo\" buyitem")
		

