#!/usr/bin/python3

# Bottle
from bottle import Bottle, run, response, static_file, request

# Импорты Python
import sys, sqlite3, configparser, os, errno, json, ipaddress, re
from urllib.parse import urlparse

# Наш конфигурационный файл
config = configparser.ConfigParser()
config.read('/etc/roskom/tools.ini')

# Костыль
def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

# База данных
db = sqlite3.connect(config['roskomtools']['database'])
db.create_function('regexp', 2, lambda x, y: 1 if re.search(x, y) else 0)
db.create_function('pow', 2, lambda x, y: x ** y)
db.row_factory = dict_factory

application = Bottle()

@application.route('/last-check')
def home_page():
	response.content_type = 'application/json; charset=utf-8'
	cursor = db.cursor()
	try:
		statement = cursor.execute("SELECT * FROM checks ORDER BY check_when DESC LIMIT 1")
	except:
		return '{}'
	result = statement.fetchall()
	if len(result) == 0:
		return '{}'
	else:
		check = result[0]
		reply = {
			'check_id': int(check['check_id']),
			'when': int(check['check_when']),
			'total_links': int(check['check_total']),
			'available_links': int(check['check_available']),
			'duration_minutes': int(check['check_minutes']),
			'duration_seconds': int(check['check_seconds']),
			'maxrss': int(check['check_maxrss']),
		}
		return json.dumps(reply)

@application.route('/last-load')
def last_load_page():
	response.content_type = 'application/json; charset=utf-8'
	cursor = db.cursor()
	try:
		statement = cursor.execute("SELECT * FROM loads ORDER BY load_when DESC LIMIT 1")
	except:
		return '{}'
	result = statement.fetchall()
	if len(result) == 0:
		return '{}'
	else:
		load = result[0]
		reply = {
			'load_id': int(load['load_id']),
			'when': int(load['load_when']),
			'state': int(load['load_state']),
			'code': load['load_code'],
		}
		return json.dumps(reply)

@application.route('/last-successful-load')
def last_successful_load_page():
	response.content_type = 'application/json; charset=utf-8'
	cursor = db.cursor()
	try:
		statement = cursor.execute("SELECT * FROM loads WHERE load_state = 0 ORDER BY load_when DESC LIMIT 1")
	except:
		return '{}'
	result = statement.fetchall()
	if len(result) == 0:
		return '{}'
	else:
		load = result[0]
		reply = {
			'load_id': int(load['load_id']),
			'when': int(load['load_when']),
			'code': load['load_code'],
		}
		return json.dumps(reply)

# рекомендуется переопределить в nginx или хотя бы в uWSGI
@application.route('/dump.xml')
def dump_xml_page():
	for i in config['api']['allow'].split(','):
		allowed_ip = ipaddress.ip_address(i)
		if allowed_ip == ipaddress.ip_address(request.environ.get('REMOTE_ADDR')):
			return static_file('dump.xml', root = '/var/lib/roskomtools', mimetype = 'text/xml')
	
	response.status = 403
	response.content_type = 'application/json; charset=utf-8'
	return json.dumps({'error': 403})

@application.route('/blocked-ips')
def blocked_ips_page():
	response.content_type = 'application/json; charset=utf-8'
	cursor = db.cursor()

	pure_ips = set()
	pure_ipsv6 = set()
	subnets = set()
	subnetsv6 = set()
	wpdomains = set()

	# Quering IPs from registry
	cursor.execute("SELECT ip_text FROM ips WHERE ip_content_id IN (SELECT content_id FROM content WHERE content_block_type = 'ip')")
	for row in cursor.fetchall():
		pure_ips.add(row['ip_text'])

	# Quering IPv6s from registry
	cursor.execute("SELECT ip_text FROM ipsv6 WHERE ip_content_id IN (SELECT content_id FROM content WHERE content_block_type = 'ip')")
	for row in cursor.fetchall():
		pure_ipsv6.add(row['ip_text'])

	# Quering IPv4 subnets from registry
	cursor.execute("SELECT subnet_text FROM subnets")
	for row in cursor.fetchall():
		subnets.add(row['subnet_text'])

	# Quering IPv6 subnets from registry
	cursor.execute("SELECT subnet_text FROM subnetsv6")
	for row in cursor.fetchall():
		subnetsv6.add(row['subnet_text'])

	# Quering wrong-port domains
	cursor.execute("SELECT url_text FROM urls WHERE url_text REGEXP '^https?://[^:/]+:[0-9]+'")
	for row in cursor.fetchall():
		try:
			info = urlparse(row['url_text'])
			wpdomains.add(info.hostname)
		except:
			continue

	return json.dumps({'ips': list(pure_ips), 'ipsv6': list(pure_ipsv6), 'subnets': list(subnets), 'subnetsv6': list(subnetsv6), 'wpdomains': list(wpdomains)})

@application.route('/blocked-ips-short')
def blocked_ips_short_page():
	response.content_type = 'application/json; charset=utf-8'
	cursor = db.cursor()

	subnets = set()
	subnetsv6 = set()
	wpdomains = set()

	# Quering IPv4 subnets from registry
	cursor.execute("SELECT subnet_text FROM subnets")
	for row in cursor.fetchall():
		subnets.add(row['subnet_text'])

	# Quering IPv6 subnets from registry
	cursor.execute("SELECT subnet_text FROM subnetsv6")
	for row in cursor.fetchall():
		subnetsv6.add(row['subnet_text'])

	# Quering wrong-port domains
	cursor.execute("SELECT url_text FROM urls WHERE url_text REGEXP '^https?://[^:/]+:[0-9]+'")
	for row in cursor.fetchall():
		try:
			info = urlparse(row['url_text'])
			wpdomains.add(info.hostname)
		except:
			continue

	return json.dumps({'subnets': list(subnets), 'subnetsv6': list(subnetsv6), 'wpdomains': list(wpdomains)})

@application.route('/ip-count')
def ip_count_page():
	response.content_type = 'application/json; charset=utf-8'
	cursor = db.cursor()
	cursor.execute("SELECT SUM(POW(2, 32 - SUBSTR(subnet_text, INSTR(subnet_text, '/') + 1))) AS c FROM subnets")
	rows = cursor.fetchall()
	return json.dumps({'count': int(rows[0]['c'])})

def describe_content_record(content, cursor):
	content_id = int(content['content_id'])
	cursor.execute("SELECT * FROM urls WHERE url_content_id = ?", (content_id,))
	content.update({'urls': cursor.fetchall()})
	cursor.execute("SELECT * FROM domains WHERE domain_content_id = ?", (content_id,))
	content.update({'domains': cursor.fetchall()})
	cursor.execute("SELECT * FROM ips WHERE ip_content_id = ?", (content_id,))
	content.update({'ips': cursor.fetchall()})
	cursor.execute("SELECT * FROM subnets WHERE subnet_content_id = ?", (content_id,))
	content.update({'subnets': cursor.fetchall()})
	cursor.execute("SELECT * FROM ipsv6 WHERE ip_content_id = ?", (content_id,))
	content.update({'ipsv6': cursor.fetchall()})
	cursor.execute("SELECT * FROM subnetsv6 WHERE subnet_content_id = ?", (content_id,))
	content.update({'subnetsv6': cursor.fetchall()})

@application.route('/record-by-id/<content_id:int>')
def search_record_by_id_page(content_id):
	response.content_type = 'application/json; charset=utf-8'
	cursor = db.cursor()
	cursor.execute("SELECT * FROM content WHERE content_id = ?", (int(content_id),))
	rows = cursor.fetchall()
	if len(rows)  == 1:
		content = rows[0]
		describe_content_record(content, cursor)
		return json.dumps(content)
	else:
		response.status = 404
		response.content_type = 'application/json; charset=utf-8'
		return json.dumps({'error': 404})

@application.route('/records-by-domain/<domain>')
def search_records_by_domain_page(domain):
	domain = '%' + domain
	response.content_type = 'application/json; charset=utf-8'
	cursor = db.cursor()
	cursor.execute("SELECT * FROM content WHERE content_id IN (SELECT domain_content_id FROM domains WHERE domain_text LIKE ?)", (domain,))
	rows = cursor.fetchall()
	if len(rows) != 0:
		for content in rows:
			describe_content_record(content, cursor)

		return json.dumps(rows)
	else:
		response.status = 404
		response.content_type = 'application/json; charset=utf-8'
		return json.dumps({'error': 404})

@application.route('/records-by-url/<url>')
def search_records_by_url_page(url):
	url = '%' + url + '%'
	response.content_type = 'application/json; charset=utf-8'
	cursor = db.cursor()
	cursor.execute("SELECT * FROM content WHERE content_id IN (SELECT url_content_id FROM urls WHERE url_text LIKE ?)", (url,))
	rows = cursor.fetchall()
	if len(rows) != 0:
		for content in rows:
			describe_content_record(content, cursor)

		return json.dumps(rows)
	else:
		response.status = 404
		response.content_type = 'application/json; charset=utf-8'
		return json.dumps({'error': 404})

@application.route('/records-by-ip/<ip>')
def search_records_by_ip_page(ip):
	response.content_type = 'application/json; charset=utf-8'
	cursor = db.cursor()
	cursor.execute("SELECT * FROM content WHERE content_id IN (SELECT ip_content_id FROM ips WHERE ip_text == ?)", (ip,))
	rows = cursor.fetchall()
	if len(rows) != 0:
		for content in rows:
			describe_content_record(content, cursor)

		return json.dumps(rows)
	else:
		response.status = 404
		response.content_type = 'application/json; charset=utf-8'
		return json.dumps({'error': 404})

@application.route('/soc-resources')
def soc_resources():
	response.content_type = 'application/json; charset=utf-8'
	cursor = db.cursor()
	cursor.execute("SELECT * FROM soc_content AS sc LEFT JOIN soc_resource AS sr ON sc.content_id = resource_content_id LEFT JOIN soc_domain AS sd ON sc.content_id = domain_content_id")
	rows = cursor.fetchall()


	if len(rows) != 0:
		for content in rows:
			content_id = int(content['content_id'])
			content.update({'ips': cursor.execute("SELECT * FROM soc_ipsubnets WHERE ipsubnet_content_id = ?", (content_id,)).fetchall()})

		return json.dumps(rows)
	else:
		response.status = 404
		response.content_type = 'application/json; charset=utf-8'
		return json.dumps({'error': 404})

if __name__ == '__main__':
	run(application, host = 'localhost', port = 8080)
