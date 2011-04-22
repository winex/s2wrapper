#!/usr/bin/env python

import httplib, urllib, re, sys, logging
from phpserialize import *

class StatsServers:

	S2GHOST = "masterserver.savage2.s2games.com"
	S2GURL = "/irc_updater/irc_stats.php"
	SALVAGEHOST = "188.40.92.72"
	SALVAGEURL = "/wwwps2/index.php"
	headers = {}

	def __init__(self):
		self.headers = {
			"User-Agent": "PHP Script",
			"Content-Type": "application/x-www-form-urlencoded"
		}


	def decode (self, response):
		return loads(response, object_hook=phpobject)

	def s2gstats (self, params):

		conn = httplib.HTTPConnection (self.S2GHOST)
		conn.request ("POST", self.S2GURL, params, self.headers)

		response = conn.getresponse()

		if response.status <> 200:
			return None

		data = response.read()
		conn.close()

		#print params
		return data

	def salvagestats (self, params):
		
		decoded = urllib.quote(params)
		stats = ("stats=%s" % (decoded))

		conn = httplib.HTTPConnection (self.SALVAGEHOST)
		conn.request ("POST", self.SALVAGEURL, stats, self.headers)

		response = conn.getresponse()

		if response.status <> 200:
			return None

		data = response.read()
		conn.close()
		#print data
		return data

if __name__ == '__main__':
	linestring = open('305386.stats', 'r').read()
	ss = StatsServers()
	#print ms.getStatistics(251700)
	#print ms.getStatistics(251700,251701)
	ss.s2gstats(linestring)
	

