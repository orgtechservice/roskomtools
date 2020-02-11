
# Сторонние пакеты
from lxml import etree

re_link = r'(https?)://(([^/]*)\.([^/:\.]*))(:(\d+))?'

def parse_ts(ts):
	return 0

def parse_registry(filename, database):
	cursor = database.cursor()

	# Очистим таблицы
	cursor.execute("DELETE FROM urls")
	cursor.execute("DELETE FROM domains")
	cursor.execute("DELETE FROM ips")
	cursor.execute("DELETE FROM subnets")
	cursor.execute("DELETE FROM ipsv6")
	cursor.execute("DELETE FROM subnetsv6")
	cursor.execute("DELETE FROM content")
	cursor.execute("DELETE FROM domain_masks")

	# Заполним их заново
	tree = etree.parse(filename)	
	records = tree.xpath('//content')
	for item in records:
		try:
			content_id = str(item.get('id', default = '0'))
			content_block_type = item.get('blockType', default = 'default')
			content_ts = parse_ts(item.get('ts', default = '0'))
			content_include_time = str(item.get('includeTime', default = ''))
			content_urgency_type = int(item.get('urgencyType', default = 0))
			content_entry_type = int(item.get('entryType', default = 0))
			content_hash = item.get('hash', default = None)
			
			try:
				decision = item.xpath('decision')[0]
				content_decision_date = decision.get('date', '')
				content_decision_number = decision.get('number', '')
				content_decision_org = decision.get('org', '')
			except:
				content_decision_date = None
				content_decision_number = None
				content_decision_org = None

			data = (content_id, content_block_type, content_include_time, content_urgency_type, content_entry_type, content_hash, content_ts, content_decision_date, content_decision_number, content_decision_org)
			cursor.execute("INSERT INTO content (content_id, content_block_type, content_include_time, content_urgency_type, content_entry_type, content_hash, content_ts, content_decision_date, content_decision_number, content_decision_org) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)

			if content_block_type == 'default':
				for url in item.xpath('url'):
					cursor.execute("INSERT INTO urls (url_content_id, url_text, url_ts) VALUES (?, ?, ?)", (content_id, url.text, url.get('ts', default = 0)))
				#for domain in item.xpath('domain'):
				#	cursor.execute("INSERT INTO domains (domain_content_id, domain_text) VALUES (?, ?)", (content_id, domain.text))
			elif content_block_type == 'ip':
				for ip in item.xpath('ip'):
					cursor.execute("INSERT INTO ips (ip_content_id, ip_text, ip_ts) VALUES (?, ?, ?)", (content_id, ip.text, ip.get('ts', 0)))
				for subnet in item.xpath('ipSubnet'):
					cursor.execute("INSERT INTO subnets (subnet_content_id, subnet_text, subnet_ts) VALUES (?, ?, ?)", (content_id, subnet.text, subnet.get('ts', default = 0)))
				for ip in item.xpath('ipv6'):
					cursor.execute("INSERT INTO ipsv6 (ip_content_id, ip_text, ip_ts) VALUES (?, ?, ?)", (content_id, ip.text, ip.get('ts', 0)))
				for subnet in item.xpath('ipv6Subnet'):
					cursor.execute("INSERT INTO subnetsv6 (subnet_content_id, subnet_text, subnet_ts) VALUES (?, ?, ?)", (content_id, subnet.text, subnet.get('ts', default = 0)))
			elif content_block_type == 'domain':
				for domain in item.xpath('domain'):
					cursor.execute("INSERT INTO domains (domain_content_id, domain_text, domain_ts) VALUES (?, ?, ?)", (content_id, domain.text, domain.get('ts', default = 0)))
			elif content_block_type == 'domain-mask':
				for domain in item.xpath('domain'):
					cursor.execute("INSERT INTO domain_masks (mask_content_id, mask_text, mask_ts) VALUES (?, ?, ?)", (content_id, domain.text, domain.get('ts', default = 0)))
			else:
				pass # ???
		except:
			continue

	cursor.close()
	database.commit()

"""
def using_wrong_port(groups):
	return (groups[5] is not None) and (int(groups[5]) in [80, 8080])

def using_wrong_port(link):
	global re_link
	m = re_link.fullmatch(link):
	if m is not None:
		groups = m.groups()
		return (groups[5] is not None) and (int(groups[5]) in [80, 8080])
	else:
		return False
"""

def load_urls(database):
	result = []
	cursor = database.cursor()
	cursor.execute("SELECT url_text FROM urls")
	rows = cursor.fetchall()
	cursor.close()

	for row in rows:
		result.append({'url': row[0], 'status': 'unknown', 'reply': None, 'code': 0})

	cursor = database.cursor()
	cursor.execute("SELECT domain_text FROM domains")
	rows = cursor.fetchall()
	cursor.close()

	for row in rows:
		result.append({'url': "http://%s/" % row[0], 'status': 'unknown', 'reply': None, 'code': 0})
	
	return result
