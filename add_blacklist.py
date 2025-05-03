import requests
from bs4 import BeautifulSoup
import time
import json
import rapidjson
from typing import Any, Dict, List, Optional
from pathlib import Path
from libs.api import FtRestClient
import logging
import sys
import re 

path_bots_file = 'bots.json'
CONFIG_PARSE_MODE = rapidjson.PM_COMMENTS | rapidjson.PM_TRAILING_COMMAS
tokens = []

bots = []
force_update = 0
from logging import Formatter
from logging.handlers import RotatingFileHandler
loop_secs = 120
ROOT_PATH = "."
DATA_PATH = ".."
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
FILE_LOGFORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)
delist_log_file = f"{ROOT_PATH}/binance_delist_info.log"
        
handler_rf = RotatingFileHandler(
	delist_log_file,
	maxBytes=1024 * 1024 * 10,  # 10Mb
	backupCount=10,
)
DEBUG = True
    
handler_rf.setFormatter(Formatter(FILE_LOGFORMAT))
logger.addHandler(handler_rf)


def open_local_blacklist(filename):
	global tokens
	tokens.clear()
	try:
		with open(filename, 'r') as file:
			for line in file:
				line = line.strip()
				# 忽略注释行和空行
				if line.startswith('//') or not line:
					continue
				tokens.append(line)
	except FileNotFoundError:
		logger.error(f"Blacklist file {filename} not found.")
	except Exception as e:
		logger.error(f"Error reading blacklist file {filename}: {e}")

def load_bots_data():
	new_bots = []
	with Path(path_bots_file).open() if path_bots_file != '-' else sys.stdin as file:
		data_bots = rapidjson.load(file, parse_mode=CONFIG_PARSE_MODE)
		for line in data_bots:
			new_bots.append(line)
	return new_bots

def send_blacklist():
    # if len(blacklist) > 0 or force_update%5 ==0:
	for bot in bots:
		logger.info(f"Fetching current blacklist from {bot['ip_address']}")
		api_bot = FtRestClient(f"http://{bot['ip_address']}", bot['username'], bot['password'])

		# 获取当前的 bot 的 blacklist
		current_blacklist = set(api_bot.blacklist()['blacklist'])

		# 找出传入的 blacklist 中 bot 目前不包含的条目
		new_blacklist_items = set(tokens) - current_blacklist

		# 如果有不一致的条目，发送更新
		if new_blacklist_items:
			logger.info(f"Updating blacklist for {bot['ip_address']} with {new_blacklist_items}")
			api_bot.blacklist(*new_blacklist_items)
		else:
			logger.info(f"No updates needed for {bot['ip_address']}")


if __name__ == "__main__":
	bots = load_bots_data()
	filename = "blacklist.txt"
	open_local_blacklist(filename)
	send_blacklist()
	starttime = time.monotonic()
	while True:
		time.sleep(loop_secs - ((time.monotonic() - starttime) % loop_secs))
		bots = load_bots_data()
		open_local_blacklist(filename)	
		send_blacklist()
		
