import os, re
import ConfigParser
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler

class vetlimit(ConsolePlugin):

	reason = "This_Server_Has_Restrictions_On"

	ms = None

	_level = -1
	_sf = -1

	def onPluginLoad(self):
		self.ms = MasterServer ()

		Config = ConfigParser.ConfigParser ()
		Config.read ('%s/vetlimit.ini' % os.path.dirname (os.path.realpath (__file__)))
		for (name, value) in Config.items ('Restrict'):
			if (name == "level"):
				self._level = int(value)

			if (name == "sf"):
				self._sf = int(value)

		pass

        def onRecievedAccountId (self, *args, **kwargs):

		if (self._level == -1 and self._sf == -1):
			return 


		id = args[0][1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		
		level = int(stats['level'])
		sf = int(stats['sf'])



		doKick = False

		if (self._level > -1 and level < self._level):
			doKick = True
			self.reason += "_Level_%s" % self._level

		if (self._sf > -1 and sf < self._sf):
			doKick = True
			self.reason += ",SF_%s" % self._sf


		if (doKick):
			kwargs['Broadcast'].put ("kick %s %s" % (args[0][0], self.reason))
			kwargs['Broadcast'].broadcast ()
