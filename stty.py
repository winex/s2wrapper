# -*- coding: utf-8 -*-


import os


debug = False


def call(arg):
	if debug:
		print("stty.call(%s)" % arg)
	return os.popen("stty %s" % (arg), "r").read()

def getSize():
	ret = call("size").split(" ")
	ret = (int(ret[0]), int(ret[1]))
	print("stty.getSize(): %s" % repr(ret))
	return ret

def setSize(size):
	print("stty.setSize(%s)" % repr(size))
	return call("rows %d cols %d" % (size[0], size[1]))
