# -*- coding: utf-8 -*-

import traceback
import sys
import os
import imp
import re
from S2Wrapper import ConsoleParser


class Plugin(object):
	def onPluginLoad(self, config):
		pass

	pass

class ConsolePlugin(Plugin, ConsoleParser, object):
	pass



_imports = []
_instances = []
_path = None

def discover(path = None):
	global _path
	if path:
		_path = path
	if not _path:
		print("%s: _path is not set" % (__name__))
		return

	print("%s: search path: %s" % (__name__, _path))
	plugins = [x[:-3] for x in os.listdir(_path) if x.endswith(".py")]
	sys.path.insert(0, _path)

	for name in plugins:
		try:
			_imports.append(__import__(name))
		except Exception as e:
			print("%s: %s produced an error: %s" % (__name__, name , e))
	return

def getEnabled(type):
	return _instances

def reload(name):
	mod = None
	for module in _imports:
		if module.__name__ == name:
			mod = module
			break

	if not mod:
		print("%s: %s not found" % (__name__, name))
		return

	disable(name)
	try:
		imp.reload(mod)
	except:
		traceback.print_exc()
		return

	return enable(name)


def disable(name):

	for inst in _instances:
		if inst.__class__.__name__ == name:

			plugin = find (name)
			if plugin is not None:
				del plugin

			_instances.remove (inst)
			del inst

			print("%s: %s has been disabled" % (__name__, name))
			return True

	print("%s: %s is not enabled" % (__name__, name))
	return False


# Yeah so.., as I can't seem to find out, how to delete modules from __subclasses__..
# I Made this nasty hack, which just takes the latest module, instead of the first.
# This means on each enable/reload this list increases in size, infinitely...
def find (pluginName):

	_plugin = None

	for type in Plugin.__subclasses__():
		for plugin in type.__subclasses__():
			if pluginName == plugin.__name__:
				_plugin = plugin

	return _plugin

def enable(name):
	cls = find(name)
	if not cls:
		print("%s: %s not found" % (__name__, name))
		return False

	try:
		inst = cls()
		_instances.append(inst)
		config = "%s.ini" % os.path.join(_path, name)
		print("%s: %s config: %s" % (__name__, name, config))
		inst.onPluginLoad(config)
	except Exception as e:
		print("%s: %s error: %s" % (__name__, name , e))
		return False

	print("%s: %s has been enabled" % (__name__, name))
	return True

def list():
	rtn = []
	for plugin in _imports:
		rtn.append(plugin.__name__)
	return rtn
