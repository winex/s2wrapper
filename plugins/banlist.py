# -*- coding: utf-8 -*-

import os
import re
import ConfigParser
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler

class banlist(ConsolePlugin):

	reason = "BANNED! :P"
	bans = {}
	regex = {}

	def onPluginLoad(self):

		config = ConfigParser.ConfigParser()
		config.read ('%s/banlist.ini' % os.path.dirname(os.path.realpath(__file__)))
		for (name, value) in config.items('banlist'):
			if name == "reason":
				self.reason = value
			elif name.startswith("regex:"):
				name = name[6:]
				print name
				self.regex[re.compile(name)] = value
			else:
				self.bans[name] = value

		print self.bans
		print self.regex

	def onSetName(self, *args, **kwargs):

		success = False
		id = args [0][0]
		nick = args [0][1]
		reason = ""

		try:
			reason = self.bans [nick]
			success = True

		except KeyError:

			success = False
			pass

		if success == False:
			for regex in self.regex:
				if regex.match (nick):
					reason = self.regex[regex]
					success = True
					break

		if success == False:
			return

		kwargs['Broadcast'].put ("kick %s %s" % (id, reason))
		kwargs['Broadcast'].broadcast ()
