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

	def onPluginLoad(self, config):
		# TODO: 20101015 winex: ConfigParser lowercases option names
		# which kills regex part especially
		ini = ConfigParser.ConfigParser()
		ini.read(config)
		for (name, value) in ini.items('banlist'):
			print("%s: %s" % (__name__, (name, value)))
			if not value:
				value = self.reason

			if name == "reason":
				self.reason = value
			elif name.startswith("@"):
				# skip '@'
				self.regex[re.compile(name[1:])] = value
			else:
				self.bans[name] = value

		print("bans : %s" % self.bans)
		print("regex: %s" % self.regex)

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

		kwargs['Broadcast'].put ("kick %s \"%s\"" % (id, reason))
		kwargs['Broadcast'].broadcast ()
