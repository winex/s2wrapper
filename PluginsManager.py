import sys
import os
import imp
import re
from S2Wrapper import ConsoleParser


class Plugin(object):
	def onPluginLoad(self):
		pass

	pass

class ConsolePlugin(Plugin, ConsoleParser, object):
	pass



_imports = []
_instances = []
def discover ():

	plugin_dir = "%s/plugins" % os.path.dirname (os.path.realpath (__file__))
	plugins = [x[:-3] for x in os.listdir(plugin_dir) if x.endswith(".py")]
	sys.path.insert (0, plugin_dir)

	for plugin in plugins:
		try:
			_imports.append (__import__(plugin))

		except Exception as e:
			print "Loading the module %s has an error: %s" % (plugin , e)

def name (module):
	return module.__name__

def getEnabled (type):
	return _instances

def reload (pluginName):
	mod = None

	for module in _imports:
		if name(module) == pluginName:
			mod = module
			break

	if mod is None:
		return False

	disable (pluginName)
	imp.reload (mod)
	enable (pluginName)


	print mod


	return True


def disable (name):

	for inst in _instances:
		if inst.__class__.__name__ == name:

			plugin = find (name)
			if plugin is not None:
				del plugin

			_instances.remove (inst)
			del inst

			return True

	return False


# Yeah so.., as I can't seem to find out, how to delete modules from __subclasses__..
# I Made this nasty hack, which just takes the latest module, instead of the first.
# This means on each enable/reload this list increases in size, infinitely...
def find (pluginName):

	_plugin = None

	for type in Plugin.__subclasses__():
		for plugin in type.__subclasses__():
			if pluginName == name(plugin):
				_plugin = plugin

	return _plugin

def enable(name):

	cls = find (name)
	if cls is not None:
		try:
			inst = cls ()
			_instances.append (inst)
			inst.onPluginLoad ()
			return True

		except Exception as e:
			print "Enabling of plugin %s produced an error: %s\n" % (name , e)

	return False

def list ():

	rtn = ""
	for plugin in _imports:
		rtn += (name(plugin) + " ")

	return rtn
