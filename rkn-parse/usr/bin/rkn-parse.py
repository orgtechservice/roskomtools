#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Импорты Python
import sys, sqlite3, configparser, os, errno


# Наш конфигурационный файл
config = configparser.ConfigParser()
config.read('/etc/roskom/tools.ini')

# Общие модули
sys.path.append('/usr/share/roskomtools')
import rknparser

# База данных
db = sqlite3.connect(config['roskomtools']['database'])

def parseForbidden():
	cursor = db.cursor()
	cursor.execute("CREATE TABLE IF NOT EXISTS content (content_id INT, content_block_type TEXT, content_include_time TEXT, content_urgency_type INT, content_entry_type INT, content_hash TEXT, content_ts INT, content_decision_date TEXT, content_decision_number TEXT, content_decision_org TEXT, PRIMARY KEY (content_id))")
	cursor.execute("CREATE TABLE IF NOT EXISTS domains (domain_content_id INT, domain_text TEXT, domain_ts INT)")
	cursor.execute("CREATE TABLE IF NOT EXISTS domain_masks (mask_content_id INT, mask_text TEXT, mask_ts INT)")
	cursor.execute("CREATE TABLE IF NOT EXISTS urls (url_content_id INT, url_text TEXT, url_ts INT)")
	cursor.execute("CREATE TABLE IF NOT EXISTS ips (ip_content_id INT, ip_text TEXT, ip_ts INT)")
	cursor.execute("CREATE TABLE IF NOT EXISTS subnets (subnet_content_id INT, subnet_text TEXT, subnet_ts INT)")
	cursor.execute("CREATE TABLE IF NOT EXISTS ipsv6 (ip_content_id INT, ip_text TEXT, ip_ts INT)")
	cursor.execute("CREATE TABLE IF NOT EXISTS subnetsv6 (subnet_content_id INT, subnet_text TEXT, subnet_ts INT)")
	cursor.execute("CREATE INDEX IF NOT EXISTS domain_content_id_idx ON domains (domain_content_id)")
	cursor.execute("CREATE INDEX IF NOT EXISTS mask_content_id_idx ON domain_masks (mask_content_id)")
	cursor.execute("CREATE INDEX IF NOT EXISTS url_content_id_idx ON urls (url_content_id)")
	cursor.execute("CREATE INDEX IF NOT EXISTS ip_content_id_idx ON ips (ip_content_id)")
	cursor.execute("CREATE INDEX IF NOT EXISTS subnet_content_id_idx ON subnets (subnet_content_id)")
	cursor.close()
	db.commit()
	print("Parsing the registry...")

	if os.isatty(sys.stdin.fileno()):
		try_process('dump.xml', db, 'forbidden')
	else:
		try_process('/var/lib/roskomtools/dump.xml', db, 'forbidden')

def parseSoc():
	cursor = db.cursor()
	cursor.execute("CREATE TABLE IF NOT EXISTS soc_content (content_id INT, content_include_time TEXT, content_hash)")
	cursor.execute("CREATE TABLE IF NOT EXISTS soc_resource (resource_content_id INT, resourceName TEXT)")
	cursor.execute("CREATE TABLE IF NOT EXISTS soc_domain (domain_content_id INT, domain TEXT)")
	cursor.execute("CREATE TABLE IF NOT EXISTS soc_ipsubnets (ipsubnet_content_id INT, ipsubnet TEXT)")
	cursor.execute("CREATE INDEX IF NOT EXISTS resource_content_id_idx ON soc_resource (resource_content_id)")
	cursor.execute("CREATE INDEX IF NOT EXISTS domaint_content_id_idx ON soc_domain (domain_content_id)")
	cursor.execute("CREATE INDEX IF NOT EXISTS ipsubnet_content_id_idx ON soc_ipsubnets (ipsubnet_content_id)")
	cursor.close()
	db.commit()
	print("Parsing the soc registry...")

	if os.isatty(sys.stdin.fileno()):
		try_process('register.xml', db, 'soc')
	else:
		try_process('/var/lib/roskomtools/register.xml', db, 'soc')


def try_process(filename, db, type):
	if type == 'forbidden':
		try:
			rknparser.parse_registry(filename, db)
		#	rknparser.resolve_all(filename, db)
		except OSError as e:
			print("dump.xml is not accessible")
		except:
			print("Parsing failed")
		else:
			print("Finished")
	elif type == 'soc':
		try:
			rknparser.parse_soc_registry(filename, db)
		#	rknparser.resolve_all(filename, db)
		except OSError as e:
			print("registry.xml is not accessible")
		except:
			print("Parsing failed")
		else:
			print("Finished")

parseForbidden()
parseSoc()