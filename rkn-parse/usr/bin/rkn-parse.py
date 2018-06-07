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
cursor.execute("CREATE TABLE IF NOT EXISTS content (content_id INT, content_block_type TEXT, PRIMARY KEY (content_id))")
cursor.execute("CREATE TABLE IF NOT EXISTS domains (domain_content_id INT, domain_text TEXT, PRIMARY KEY (domain_content_id))")
cursor.execute("CREATE TABLE IF NOT EXISTS urls (url_content_id INT, url_text TEXT, PRIMARY KEY (url_content_id))")
cursor.execute("CREATE TABLE IF NOT EXISTS ips (ip_content_id INT, ip_text TEXT, PRIMARY KEY (ip_content_id))")
cursor.execute("CREATE TABLE IF NOT EXISTS subnets (subnet_content_id INT, subnet_text TEXT, PRIMARY KEY (subnet_content_id))")
cursor.close()
db.commit()

parser.parse_registry('dump.xml', db)

print("Finished")
