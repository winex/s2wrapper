# -*- coding: utf-8 -*-

import os
import re
import MySQLdb

from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler


class ladder(ConsolePlugin):

	debug = True
	version = "1.0"

	def onPluginLoad(self, config):
		self.config = config
		print("ladder version: %s" % (self.version))

	def onMessage (self, *args, **kwargs):
		pass

	def onSGame (self, *args, **kwargs):
		self.saveLadder (args[0]);


	def saveLadder (self, serverstring):
		if self.debug:
			print serverstring

		chunks = serverstring.split (' ');
		if len(chunks) != 4 or chunks[0] != 'LADDER':
			return

		map = chunks[1]
		command = chunks[2]
		message = chunks[3]
		message = message.strip ('%')

		winner = []
		loser = []
		(winner , loser) = message.split ('$')


		w_player_id = 0
		l_player_id = 0
		w_unit = ""
		l_unit = ""
		w_hp_start = 0
		l_hp_start = 0
		w_hp_end = 0
		(w_player_id, w_unit, w_hp_start, w_hp_end) = winner.split (',')
		(l_player_id, l_unit, l_hp_start) = loser.split (',')

		w_unit = w_unit.replace ('Player_', '').lower ()
		l_unit = l_unit.replace ('Player_', '').lower ()

		if self.debug:
			print "w_player_id: %s\n w_unit: %s\n w_hp_start: %s\n w_hp_end: %s" % (w_player_id, w_unit, w_hp_start, w_hp_end)
			print "l_player_id: %s\n l_unit: %s\n l_hp_start: %s" % (l_player_id, l_unit, l_hp_start)

		db = MySQLdb.connect(host="", user="", passwd="", db="")
		c = db.cursor()

		c.execute ("""
			INSERT INTO `s2_match` (`ctime`) VALUE (UNIX_TIMESTAMP());
		""")
		match_id = db.insert_id ()

		c.execute ("""
			SELECT 1 FROM `s2_player` WHERE id = %s LIMIT 1
		""", (w_player_id, ))
		if c.fetchone () is None:
			c.execute ("""
				INSERT INTO `s2_player` 
				    (`id`, `ctime`)
			        VALUES
				    (%s , UNIX_TIMESTAMP())
			""", (w_player_id, ))

		c.execute ("""
			SELECT 1 FROM `s2_player` WHERE id = %s LIMIT 1
		""", (l_player_id, ))
		if c.fetchone () is None:
			c.execute ("""
				INSERT INTO `s2_player` 
				    (`id`, `ctime`)
			        VALUES
				    (%s , UNIX_TIMESTAMP())
			""", (l_player_id, ))


		query_loser = "INSERT INTO `s2_match_player` (`match_id`, `player_id`, `unit`, `hp_start`, `ctime`) VALUES (%s , %s , '%s' , %s, UNIX_TIMESTAMP())" % (match_id , l_player_id, l_unit, l_hp_start)
		query_winner = "INSERT INTO `s2_match_player` (`match_id`, `player_id`, `unit`, `hp_start`, `hp_end`, `ctime`) VALUES (%s , %s , '%s' , %s, %s, UNIX_TIMESTAMP())" % (match_id , w_player_id, w_unit, w_hp_start, w_hp_end)

		c.execute (query_winner)
		c.execute (query_loser)
