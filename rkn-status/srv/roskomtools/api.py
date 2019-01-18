#!/usr/bin/python3

# Bottle
from bottle import Bottle, run, response, static_file, request

# Импорты Python
import sys, sqlite3, configparser, os, errno, json, ipaddress

# Наш конфигурационный файл
config = configparser.ConfigParser()
config.read('/etc/roskom/tools.ini')

# База данных
db = sqlite3.connect(config['roskomtools']['database'])

application = Bottle()

@application.route('/last-check')
def home_page():
	response.content_type = 'text/plain'
	cursor = db.cursor()
	try:
		statement = cursor.execute("SELECT check_id, check_when, check_total, check_available, check_minutes, check_seconds, check_maxrss FROM checks ORDER BY check_when DESC LIMIT 1")
	except:
		return '{}'
	result = statement.fetchall()
	if len(result) == 0:
		return '{}'
	else:
		check = result[0]
		reply = {
			'check_id': int(check[0]),
			'when': int(check[1]),
			'total_links': int(check[2]),
			'available_links': int(check[3]),
			'duration_minutes': int(check[4]),
			'duration_seconds': int(check[5]),
			'maxrss': int(check[6]),
		}
		return json.dumps(reply)

@application.route('/last-load')
def last_load_page():
	response.content_type = 'text/plain'
	cursor = db.cursor()
	try:
		statement = cursor.execute("SELECT load_id, load_when, load_state, load_code FROM loads ORDER BY load_when DESC LIMIT 1")
	except:
		return '{}'
	result = statement.fetchall()
	if len(result) == 0:
		return '{}'
	else:
		load = result[0]
		reply = {
			'check_id': int(load[0]),
			'when': int(load[1]),
			'state': int(load[2]),
			'code': load[3],
		}
		return json.dumps(reply)

@application.route('/last-successful-load')
def last_successful_load_page():
	response.content_type = 'text/plain'
	cursor = db.cursor()
	try:
		statement = cursor.execute("SELECT load_id, load_when, load_code FROM loads WHERE load_state = 0 ORDER BY load_when DESC LIMIT 1")
	except:
		return '{}'
	result = statement.fetchall()
	if len(result) == 0:
		return '{}'
	else:
		load = result[0]
		reply = {
			'check_id': int(load[0]),
			'when': int(load[1]),
			'code': load[2],
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
	response.content_type = 'text/plain'
	return json.dumps({'error': 403})


if __name__ == '__main__':
	run(app, host = 'localhost', port = 8080)
