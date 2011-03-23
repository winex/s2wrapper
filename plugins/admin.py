# -*- coding: utf-8 -*-
# 3.22.11 - First version of admin plugin
import re
import math
import time
import ConfigParser
import threading
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler
from operator import itemgetter

#This plugin was written by Old55 and he takes full responsibility for the junk below.
#He does not know python so the goal was to make something functional, not something
#efficient or pretty.


class admin(ConsolePlugin):
	VERSION = "1.0.0"
	playerlist = []
	adminlist = []
	banlist = []
	PHASE = 0

	def onPluginLoad(self, config):
		self.ms = MasterServer ()

		ini = ConfigParser.ConfigParser()
		ini.read(config)
		for (name, value) in ini.items('admin'):
			self.adminlist.append(name)
		print self.adminlist
	def getPlayerByClientNum(self, cli):

		for client in self.playerlist:
			if (client['clinum'] == cli):
				return client

	def getPlayerByName(self, name):

		for client in self.playerlist:
			if (client['name'].lower() == name.lower()):
				return client

	def onConnect(self, *args, **kwargs):
		
		id = args[0]
		ip = str(args[2])
		print self.banlist

		reason = "An administrator has removed you from this server. You may rejoin the server after the current game ends."
		
		for each in self.banlist:
			if each == ip:
				kwargs['Broadcast'].broadcast("Kick %s \"%s\"" % (id, reason))

		for client in self.playerlist:
			if (client['clinum'] == id):
				return
		
		self.playerlist.append ({'clinum' : id, 'acctid' : 0, 'name' : 'X', 'ip' : ip})
	

	def onSetName(self, *args, **kwargs):
		
		cli = args[0]
		playername = args[1]
		client = self.getPlayerByClientNum(cli)
		client ['name'] = playername

					
	def onAccountId(self, *args, **kwargs):

		cli = args[0]
		id = args[1]
				
		client = self.getPlayerByClientNum(cli)

				
		if self.isAdmin(client, **kwargs):
			kwargs['Broadcast'].broadcast("SendMessage %s ^cYou are registered as an administrator. Send the chat message: ^rhelp ^cto see what commands you can perform." % (cli))

		
	def isAdmin(self, client, **kwargs):
		admin = False
		
		for each in self.adminlist:
			if client['name'].lower() == each:
				admin = True
		
		return admin

	def onMessage(self, *args, **kwargs):
		
		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
		admin = self.isAdmin(client, **kwargs)

		#ignore everything if it isn't from admin
		if not admin:
			return

		restart = re.match("restart", message, flags=re.IGNORECASE)
		shuffle = re.match("shuffle", message, flags=re.IGNORECASE)
		kick = re.match("kick (\S+)", message, flags=re.IGNORECASE)
		changeworld = re.match("changeworld (\S+)", message, flags=re.IGNORECASE)
		help = re.match("help", message, flags=re.IGNORECASE)
		prevphase = re.match("previous phase", message, flags=re.IGNORECASE)
		
		if restart:
			#restarts server if something catastrophically bad has happened
			kwargs['Broadcast'].broadcast("restart")

		if shuffle:
			#currently unused, but could be used to force shuffle vote
			print "shuffle called"
						
			
		if kick:
			#kicks a player from the server and temporarily bans that player's IP till the game is over
			reason = "An administrator has removed you from the server, probably for being annoying"
			kickclient = self.getPlayerByName(kick.group(1))
			kwargs['Broadcast'].broadcast("Kick %s \"%s\"" % (kickclient['clinum'], reason))
			self.banlist.append(client['ip'])

		if changeworld:
			#change the map
			kwargs['Broadcast'].broadcast("changeworld %s" % (changeworld.group(1)))

		if prevphase:
			#if game is started, move back to previous phase
			if self.PHASE != 5:
				kwargs['Broadcast'].broadcast("SendMessage %s Cannot change phase if the game has not started!" % (client['clinum']))
				return

			kwargs['Broadcast'].broadcast("prevphase")

		self.logCommand(client['name'],message)

		if help:
			kwargs['Broadcast'].broadcast("SendMessage %s All commands on the server are done through server chat. All commands are logged to prevent you from abusing them.The following are commands and a short description of what they do." % (client['clinum']))
			kwargs['Broadcast'].broadcast("SendMessage %s ^rrestart ^whard reset of the server. ONLY use in weird cases." % (client['clinum']))
			kwargs['Broadcast'].broadcast("SendMessage %s ^rshuffle ^wis currently unimplemented, but it will shuffle the game and set to previous phase." % (client['clinum']))
			kwargs['Broadcast'].broadcast("SendMessage %s ^rkick playername ^wwill remove a player from the server and ban that IP address till the end of the game." % (client['clinum']))
			kwargs['Broadcast'].broadcast("SendMessage %s ^rchangeworld mapname ^wwill change the map to the desired map." % (client['clinum']))
			kwargs['Broadcast'].broadcast("SendMessage %s ^rprevious phase ^wwill reset the map and set the game to the previous phase. May be better than changeworld if you are restarting a stacked game." % (client['clinum']))
	
	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		self.PHASE = phase

		if (phase == 6):
			self.banlist = []	

	def logCommand(self, client, message, **kwargs):
		localtime = time.localtime(time.time())
		date = ("%s-%s-%s, %s:%s:%s" % (localtime[1], localtime[2], localtime[0], localtime[3], localtime[4], localtime[5]))
		f = open('admin.log', 'a')		
		f.write("Timestamp: \"%s\", Admin: %s, Command: %s\n" % (date, client, message))
		f.close
