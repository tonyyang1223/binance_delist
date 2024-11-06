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
url = "https://www.binance.com/en/support/announcement/delisting?c=161&navId=161"
path_blacklist_file = 'blacklist.json'
path_processed_file = 'processed.json'
path_bots_file = 'bots.json'
CONFIG_PARSE_MODE = rapidjson.PM_COMMENTS | rapidjson.PM_TRAILING_COMMAS
tokens = []
has_been_processed = []
bots = []

from logging import Formatter
from logging.handlers import RotatingFileHandler
loop_secs = 90
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
handler_rf.setFormatter(Formatter(FILE_LOGFORMAT))
logger.addHandler(handler_rf)

def get_delist_tokens(url):
	class_p_list_coins = "css-zwb0rk"
	new_blacklist = []
	new_processed = []
	try:
		logger.info("Scrape delisting page")
		response = requests.get(url)
		response.raise_for_status()  # 如果请求失败将会抛出异常
		count_notice = 5
		html_source = response.text
		soup = BeautifulSoup(html_source, "html.parser")
		script_tag = soup.find("script", {"id": "__APP_DATA", "type": "application/json"})
		if not script_tag:
			logger.error("Unable to find the JSON data in the <script> tag.")
			return
		
		# 解析 JSON 数据
		json_data = json.loads(script_tag.string)
		
		# 查找 articles 列表
		for catalog in json_data["appState"]["loader"]["dataByRouteId"]["d9b2"]["catalogs"]:            
		
			# 遍历并解析每个文章条目
			for article in catalog["articles"]:
				article_id = article.get("id")
				code = article.get("code")
				title = article.get("title", "").upper()
				article_type = article.get("type")
				release_date = article.get("releaseDate")
				
				if title and (title not in has_been_processed) and (title not in new_processed):
					new_processed.append(title)
					if "BINANCE WILL DELIST " in title:

						logger.info(f"New title : {title}")
						title = title.replace("BINANCE WILL DELIST ", "")
						arr_title = title.split(" ON ")
						arr_coins = arr_title[0].split(", ")
						for coin in arr_coins:
							blacklist = f"{coin}/.*"
							if (blacklist not in tokens) and (blacklist not in new_blacklist):
								new_blacklist.append(blacklist)
					elif ("NOTICE OF REMOVAL OF " in title) and ("MARGIN" not in title) and (count_notice > 0):
						
						count_notice -= 1
						formatted_title = title.lower().replace(" ", "-")
						new_url = f"https://www.binance.com/en/support/announcement/{formatted_title}-{code}"
						logger.info(f"NOTICE OF REMOVAL OF  url {new_url}")
						try:
							new_response = requests.get(new_url)
							new_response.raise_for_status()
							
							# 进一步处理新 URL 的内容
							new_soup = BeautifulSoup(new_response.text, "html.parser")
							meta_tags = new_soup.head.find_all("meta", content=True)
							
							for meta in meta_tags:
								content = meta.get("content", "")
								if "Binance will remove" in content:
									logger.info(f"Found delisting notice: {content}")
									
									# 使用正则表达式提取交易对
									pairs = re.findall(r'\b[A-Z]+/[A-Z]+\b', content)
									logger.info(f"Extracted pairs: {pairs}")
									# 将 pairs 添加到黑名单列表，或执行其他处理
									
									for coin in pairs:
										coin = coin.strip()
										if (not coin in tokens) and (not coin in new_blacklist):
											new_blacklist.append(coin)   
						except requests.RequestException as e:
							logger.error(f"Failed to fetch new URL: {new_url}")
							logger.error(e)
		if len(new_processed) > 0:
			has_been_processed.extend(new_processed)
			save_local_processed()

		if len(new_blacklist) > 0:
			tokens.extend(new_blacklist)
			save_local_blacklist()
			send_blacklist(new_blacklist)

	except Exception as e:
		logger.error("Failed to get article list.")
		logger.error(e)


def open_local_blacklist():

	try:
		logger.info("Loading local blacklist file")
		# Read config from stdin if requested in the options
		with Path(path_blacklist_file).open() if path_blacklist_file != '-' else sys.stdin as file:
			config = rapidjson.load(file, parse_mode=CONFIG_PARSE_MODE)
			for line in config['pair_blacklist']:
				tokens.append(line)
	except FileNotFoundError:
		logger.error(
			f'Config file "{path_blacklist_file}" not found!'
			' Please create a config file or check whether it exists.')
	except rapidjson.JSONDecodeError as e:
		
		logger.error(
			f'{e}\n'
			f'Please verify the following segment of your configuration:\n'
			f'Please verify your configuration file for syntax errors.'
		)

	
def save_local_blacklist():
	logger.info("Saving local blacklist file")
	try:
		new_blacklist = dict()
		new_blacklist['pair_blacklist'] = tokens
		json_obj = rapidjson.dumps(new_blacklist)
		with open(path_blacklist_file, "w") as outfile:
			outfile.write(json_obj)
	except Exception as e:
		logger.info(e)


def open_local_processed():
	logger.info("Loading local processed file")
	try:
		# Read config from stdin if requested in the options
		with Path(path_processed_file).open() if path_processed_file != '-' else sys.stdin as file:
			config = rapidjson.load(file, parse_mode=CONFIG_PARSE_MODE)
			for line in config['processed']:
				has_been_processed.append(line)
	except FileNotFoundError:
		logger.error(
			f'Config file "{path_processed_file}" not found!'
			' Please create a config file or check whether it exists.')
	except rapidjson.JSONDecodeError as e:
		logger.error(
			f'{e}\n'
			f'Please verify the following segment of your configuration:\n'
			f'Please verify your configuration file for syntax errors.'
		)

	
def save_local_processed():
	logger.info("Saving local processed file")
	try:
		new_processed = dict()
		new_processed['processed'] = has_been_processed
		json_obj = rapidjson.dumps(new_processed)
		with open(path_processed_file, "w") as outfile:
			outfile.write(json_obj)
	except Exception as e:
		logger.info(e)


def load_bots_data():
	with Path(path_bots_file).open() if path_bots_file != '-' else sys.stdin as file:
		data_bots = rapidjson.load(file, parse_mode=CONFIG_PARSE_MODE)
		for line in data_bots:
			bots.append(line)


def send_blacklist(blacklist):
	if len(blacklist) > 0:
		for bot in bots:
			logger.info(f"Send blacklist list to {bot['ip_address']}")
			api_bot = FtRestClient(f"http://{bot['ip_address']}", bot['username'], bot['password'])
			for line in blacklist:
				api_bot.blacklist(line)


if __name__ == "__main__":
	load_bots_data()
	open_local_blacklist()
	send_blacklist(tokens)
	open_local_processed()

	starttime = time.monotonic()
	while True:
		get_delist_tokens(url)
		time.sleep(loop_secs - ((time.monotonic() - starttime) % loop_secs))