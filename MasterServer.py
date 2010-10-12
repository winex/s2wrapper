#!/usr/bin/env python

import httplib, urllib, re, sys, logging
from phpserialize import *

class MasterServer:

	MASTERHOST = "masterserver.savage2.s2games.com"
	MASTERURL = "/irc_updater/irc_requester.php"
	headers = {}

	def __init__(self):
		self.headers = {
			"User-Agent": "PHP Script",
			"Content-Type": "application/x-www-form-urlencoded"
		}


	def getStatistics (self, *args):
		stub = "&account_id[%s]=%s"
		lookup = ""

		i = 0
		for id in args:
			lookup = lookup + (stub % (i, id))
			i = i + 1

		return self.decode (self.query ("f=get_all_stats%s" % lookup))

	def decode (self, response):
		return loads(response, object_hook=phpobject)

	def query (self, params):

		conn = httplib.HTTPConnection (self.MASTERHOST)
		conn.request ("POST", self.MASTERURL, params, self.headers)

		response = conn.getresponse()

		if response.status <> 200:
			return None

		data = response.read()
		conn.close()

		return data



if __name__ == '__main__':
	ms = MasterServer()
	print ms.getStatistics(251700)
	print ms.getStatistics(251700,251701)
	"""
	{'all_stats': {251700: {'demo': 1, 'overall_r': '1218', 'gold': '3771986', 'deaths': '14350', 'razed': '948', 'c_d_conns': '0', 'souls': '239', 'c_hp_repaired': '0', 'c_buffs': '238', 'c_secs': '5782', 'c_hp_healed': '7473', 'clan_img': 'png', 'c_winstreak': '0', 'earned_exp': '1815522', 'malphas': '2', 'lf': '0', 'bdmg': '4175764', 'c_gold': '263480', 'c_debuffs': '170', 'c_orders': '91', 'res': '457', 'c_losses': '2', 'c_exp': '10187', 'c_pdmg': '4446', 'c_wins': '2', 'c_kills': '17', 'total_secs': '1199039', 'revenant': '2', 'account_id': '251700', 'kills': '12685', 'cr_fk': '0.00', 'c_assists': '0', 'hp_repaired': '677835', 'npc': '906', 'clan_name': 'Heroes-of-Newerth', 'c_builds': '59', 'assists': '14052', 'c_swtch': '0', 'c_razed': '47', 'd_conns': '166', 'clan_tag': 'HoN', 'swtch': '1', 'level': '43', 'wins': '374', 'losses': '473', 'c_earned_exp': '9226', 'pdmg': '7915208', 'secs': '1199039', 'devourer': '2', 'karma': '78', 'exp': '1987781', 'hp_healed': '207573', 'sf': '118'}}}
	{'all_stats': {251700: {'demo': 1, 'overall_r': '1218', 'gold': '3771986', 'deaths': '14350', 'razed': '948', 'c_d_conns': '0', 'souls': '239', 'c_hp_repaired': '0', 'c_buffs': '238', 'c_secs': '5782', 'c_hp_healed': '7473', 'clan_img': 'png', 'c_winstreak': '0', 'earned_exp': '1815522', 'malphas': '2', 'lf': '0', 'bdmg': '4175764', 'c_gold': '263480', 'c_debuffs': '170', 'c_orders': '91', 'res': '457', 'c_losses': '2', 'c_exp': '10187', 'c_pdmg': '4446', 'c_wins': '2', 'c_kills': '17', 'total_secs': '1199039', 'revenant': '2', 'account_id': '251700', 'kills': '12685', 'cr_fk': '0.00', 'c_assists': '0', 'hp_repaired': '677835', 'npc': '906', 'clan_name': 'Heroes-of-Newerth', 'c_builds': '59', 'assists': '14052', 'c_swtch': '0', 'c_razed': '47', 'd_conns': '166', 'clan_tag': 'HoN', 'swtch': '1', 'level': '43', 'wins': '374', 'losses': '473', 'c_earned_exp': '9226', 'pdmg': '7915208', 'secs': '1199039', 'devourer': '2', 'karma': '78', 'exp': '1987781', 'hp_healed': '207573', 'sf': '118'}, 251701: {'demo': 1, 'overall_r': '0', 'gold': '5071', 'deaths': '37', 'razed': '0', 'c_d_conns': '0', 'souls': '0', 'c_hp_repaired': '0', 'c_buffs': '0', 'c_secs': '0', 'c_hp_healed': '0', 'clan_img': None, 'c_winstreak': '0', 'earned_exp': '4330', 'malphas': '0', 'lf': '0', 'bdmg': '2946', 'c_gold': '0', 'c_debuffs': '0', 'c_orders': '0', 'res': '1', 'c_losses': '0', 'c_exp': '0', 'c_pdmg': '0', 'c_wins': '0', 'c_kills': '0', 'total_secs': '4571', 'revenant': '0', 'account_id': '251701', 'kills': '14', 'cr_fk': '0.00', 'c_assists': '0', 'hp_repaired': '18013', 'npc': '1', 'clan_name': None, 'c_builds': '0', 'assists': '19', 'c_swtch': '0', 'c_razed': '0', 'd_conns': '3', 'clan_tag': None, 'swtch': '0', 'level': '1', 'wins': '1', 'losses': '3', 'c_earned_exp': '0', 'pdmg': '8599', 'secs': '4571', 'devourer': '0', 'karma': '0', 'exp': '4664', 'hp_healed': '3872', 'sf': '43'}}}
	"""
