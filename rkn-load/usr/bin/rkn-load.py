#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Python
import sys, base64, signal, time, zipfile, os, configparser, sqlite3

# SUDS
from suds.client import Client
from suds.sax.text import Text

# Наш конфигурационный файл
config = configparser.ConfigParser()
config.read('/etc/roskom/tools.ini')

# База данных
db = sqlite3.connect(config['roskomtools']['database'])

cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS loads (load_id INTEGER PRIMARY KEY AUTOINCREMENT, load_when INTEGER, load_code TEXT, load_state INTEGER)")
cursor.close()
db.commit()

def file_get_contents(filename):
	try:
		with open(filename, 'rb') as f:
			data = f.read()
	except Exception as e:
		print(e)
		return b''
	else:
		return data

class RoskomAPI:
	def __init__(self, url):
		self.url = url
		# Загрузим данные из файлов
		request_xml = file_get_contents('/etc/roskom/request.xml')
		request_xml_sign = file_get_contents('/etc/roskom/request.xml.sign')

		# Представим данные в нужном виде
		self.request_xml = base64.b64encode(request_xml).decode('utf-8')
		self.request_xml_sign = base64.b64encode(request_xml_sign).decode('utf-8')

		self.client = Client(url)
		self.service = self.client.service

	def getLastDumpDate(self):
		return self.service.getLastDumpDate()

	def sendRequest(self):
		response = self.service.sendRequest(self.request_xml, self.request_xml_sign, '2.2')
		return dict(((k, v.encode('utf-8')) if isinstance(v, Text) else (k, v)) for (k, v) in response)

	def getResult(self, code):
		response = self.service.getResult(code)
		return dict(((k, v.encode('utf-8')) if isinstance(v, Text) else (k, v)) for (k, v) in response)

class Command(object):
	client = None
	service = None
	code = None
	api = None
	console = True

	def print_message(self, message):
		if self.console:
			print(message)

	def handle_signal(self, signum, frame):
		print("Exitting on user's request")
		exit(0)

	def handle_exception(self, e):
		print(str(e))
		exit(-1)

	def handle(self, db, console = True):
		self.console = console
		signal.signal(signal.SIGTERM, self.handle_signal)
		signal.signal(signal.SIGQUIT, self.handle_signal)
		signal.signal(signal.SIGINT, self.handle_signal)

		url = 'http://vigruzki.rkn.gov.ru/services/OperatorRequest/?wsdl'

		try:
			self.print_message("Connecting to the API")
			self.api = RoskomAPI(url)
			self.print_message("API connection succeeded")
		except Exception as e:
			self.handle_exception(e)

		if self.api.request_xml == "" or self.api.request_xml_sign == "":
			self.print_message("No data in request.xml or in request.xml.sign")
			exit(-1)

		# Фактическая и записанная даты, можно сравнивать их и в зависимости от этого делать выгрузку, но мы сделаем безусловную
		try:
			dump_date = int(int(self.api.getLastDumpDate()) / 1000)
			our_last_dump = 0

			if dump_date > our_last_dump:
				self.print_message("New registry dump available, proceeding")
			else:
				self.print_message("No changes in dump.xml, but forcing the process")
		except Exception as e:
			self.handle_exception(e)

		cursor = db.cursor()
		when = int(time.time())
		data = (when, '', 1)
		cursor.execute("INSERT INTO loads (load_when, load_code, load_state) VALUES (?, ?, ?)", data)
		load_id = cursor.lastrowid
		cursor.close()
		db.commit()

		try:
			self.print_message("Sending request")
			response = self.api.sendRequest()
			self.print_message("Request sent")
			self.code = response['code'].decode('utf-8')
		except Exception as e:
			self.handle_exception(e)

		cursor = db.cursor()
		data = (self.code, load_id)
		cursor.execute("UPDATE loads SET load_code = ?, load_state = 2 WHERE load_id = ?", data)
		cursor.close()
		db.commit()

		try:
			delay = int(config['load']['delay'])
		except:
			delay = 30
	
		while True:
			self.print_message("Waiting %d seconds" % (delay,))
			time.sleep(delay)
			self.print_message("Checking result")
			result = None
			try:
				result = self.api.getResult(self.code)
			except Exception as e:
				self.handle_exception(e)

			if (result is not None) and ('result' in result) and result['result']:
				try:
					self.print_message("Got proper result, writing zip file")
					filename = "registry.zip"
					zip_archive = result['registerZipArchive']
					data = base64.b64decode(zip_archive)
					with open(filename, 'wb') as file:
						data = base64.b64decode(zip_archive)
						file.write(data)
					self.print_message("ZIP file saved")

					with zipfile.ZipFile(filename, 'r') as file:
						if self.console:
							file.extractall()
						else:
							file.extractall('/var/lib/roskomtools')
					
					cursor = db.cursor()
					cursor.execute("UPDATE loads SET load_state = 0 WHERE load_id = ?", (load_id,))
					cursor.close()
					db.commit()

					self.print_message("ZIP file extracted")
					self.print_message("Job done!")
					break
				except Exception as e:
					self.handle_exception(e)
			else:
				try:
					if result['resultComment'].decode('utf-8') == 'запрос обрабатывается':
						self.print_message("Still not ready")
						continue
					else:
						error = result['resultComment'].decode('utf-8')
						self.print_message("getRclientesult failed with code %d: %s" % (result['resultCode'], error))
						exit(-1)
				except Exception as e:
					self.handle_exception(e)

if __name__ == '__main__':
	command = Command()
	console = os.isatty(sys.stdin.fileno())
	command.handle(db, console)
