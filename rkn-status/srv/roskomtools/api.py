#!/usr/bin/python3

# Bottle
from bottle import Bottle, run, response

# Импорты Python
import sys, sqlite3, configparser, os, errno, json

# Наш конфигурационный файл
config = configparser.ConfigParser()
config.read('/etc/roskom/parse.ini')

# База данных
db = sqlite3.connect(config['parse']['database'])

application = Bottle()

@application.route('/')
def home_page():
	response.content_type = 'text/plain'
	cursor = db.cursor()
	statement = cursor.execute("SELECT check_id, check_when, check_total, check_available, check_minutes, check_seconds, check_maxrss FROM checks ORDER BY check_when DESC LIMIT 1")
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

if __name__ == '__main__':
	run(app, host = 'localhost', port = 8080)
