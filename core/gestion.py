import os
from core import file

class bcolors:
	end = '\033[0m'
	black = '\033[30m'
	white = '\033[37m'
	red = '\033[31m'
	green = '\033[32m'
	yellow = '\033[33m'
	blue = '\033[34m'
	purple = '\033[35m'
	lightblue = '\033[36m'

# CONFIGURATION
path = f"{os.path.realpath(os.path.dirname(__file__))}/../config/"
pathfile = f"{path}config.json"

if not file.exist(path):
	file.createdir(path)

if not file.exist(pathfile):
	file.create(pathfile)
	data = '{"version": "1.1", "name": "DB API", "key": "INSERT PRIVATE KEY HERE"}'
	file.write(pathfile, data)

