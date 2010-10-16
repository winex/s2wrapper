# -*- coding: utf-8 -*-

import os
import re
import ConfigParser
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler


# TODO: 20101014 winex: improve forcespec'ing player by watching inside onSetTeam
class limit(ConsolePlugin):

	CONFIG_DEFAULT = {
		'reason': "This server has restrictions on",
		'level_min': 10,
		'level_max': 100,
		'sf_min': 50,
		'sf_max': 500,
		'forcespec': False,
	}

	def onPluginLoad(self, config):
		self.config = self.CONFIG_DEFAULT.copy()
		self.ms = MasterServer()

		print(self.config)
		ini = ConfigParser.ConfigParser()
		ini.read(config)
		for name in self.config.keys():
			try:
				self.config[name] = ini.get('limit', name)
			except:
				raise
		print(self.config)

		pass

	def onReceivedAccountId(self, *args, **kwargs):
		config = self.config
		reason = config['reason']

		clnum = int(args[0][0])
		id    = int(args[0][1])

		stats = self.ms.getStatistics("%d" % (id)).get('all_stats').get(id)
		lv = int(stats['level'])
		sf = int(stats['sf'])

		act = False

		if (lv < config['level_min']) or (lv > config['level_max']):
			act = True
			reason += ". Level %d - %d only" % (config['level_min'], config['level_max'])

		if (sf < config['sf_min']) or (sf > config['sf_max']):
			act = True
			reason += ". SF %d - %d only" % (config['sf_min'], config['sf_max'])

		if not act:
			return

		if not config['forcespec']:
			kwargs['Broadcast'].put("kick %d \"%s\"" % (args[0][0], reason))
		else:
			kwargs['Broadcast'].put("SendMessage %d \"%s\"" % (clnum, reason))
			kwargs['Broadcast'].put("SetTeam #GetIndexFromClientNum(%d)# 0" % (clnum))
		kwargs['Broadcast'].broadcast()

		return
