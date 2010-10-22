# -*- coding: utf-8 -*-


import os


debug = False


def call(arg):
	if debug:
		print("stty.call(%s)" % arg)
	return os.popen("stty %s" % (arg), "r").read()

def getSize():
	ret = call("size").split(" ")
	ret = (int(ret[1]), int(ret[0]))
	print("stty.getSize(): %s" % repr(ret))
	return ret

def setSize(size):
	print("stty.setSize(%s)" % repr(size))
	return call("cols %d rows %d" % (size[0], size[1]))
