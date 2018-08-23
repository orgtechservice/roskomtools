#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Импорты Python
import sys, sqlite3, configparser

# Наш конфигурационный файл
config = configparser.ConfigParser()
config.read('/etc/roskom/parse.ini')

# Общие модули
sys.path.append('/usr/share/roskomtools')
from rknparse import parser

# База данных
db = sqlite3.connect(config['parse']['database'])

cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS content (content_id INT, content_block_type TEXT, content_include_time TEXT, content_urgency_type INT, content_entry_type INT, content_hash TEXT, content_ts INT, content_decision_date TEXT, content_decision_number TEXT, content_decision_org TEXT, PRIMARY KEY (content_id))")
cursor.execute("CREATE TABLE IF NOT EXISTS domains (domain_content_id INT, domain_text TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS domain_masks (mask_content_id INT, mask_text TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS urls (url_content_id INT, url_text TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS ips (ip_content_id INT, ip_text TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS subnets (subnet_content_id INT, subnet_text TEXT)")
cursor.execute("CREATE INDEX IF NOT EXISTS domain_content_id_idx ON domains (domain_content_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS mask_content_id_idx ON domain_masks (mask_content_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS url_content_id_idx ON urls (url_content_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS ip_content_id_idx ON ips (ip_content_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS subnet_content_id_idx ON subnets (subnet_content_id)")
cursor.close()
db.commit()

print("Parsing the registry...")

parser.parse_registry('dump.xml', db)

print("Finished")
