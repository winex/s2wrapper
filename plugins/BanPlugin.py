import os, re
import ConfigParser
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler

class BanPlugin(ConsolePlugin):

	bans = {}
	regex = {}

	def onPluginLoad(self):

		Config = ConfigParser.ConfigParser ()
		Config.read ('%s/BanPlugin.ini' % os.path.dirname (os.path.realpath (__file__)))
		for section in Config.sections ():

			for (name, value) in  Config.items (section):
				if section == "nick":
					self.bans [name] = value
				elif section == "regex":
					print name
					self.regex [re.compile(name)] = value

		print self.bans;
		print self.regex;

	def onSetName (self, *args, **kwargs):

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
