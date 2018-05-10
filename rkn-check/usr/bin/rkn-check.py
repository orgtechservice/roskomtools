#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Импорты Python
import time, sys, threading, signal, ipaddress, gc

# Сторонние пакеты
import requests
from lxml import etree

# Наш конфигурационный файл
sys.path.append('/etc/roskom')
import config

# Время начала работы скрипта
execution_start = time.time()

# Расставим затычки-мьютексы
in_mutex = threading.Lock()
out_mutex = threading.Lock()

# Прикинемся браузером
request_headers = {
	'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/49.0.2623.108 Chrome/49.0.2623.108 Safari/537.36',
}

# Счётчик обработанных ссылок (для отображения прогресса)
counter = 0

# Наш воркер
class Worker(threading.Thread):
	def __init__(self, thread_id, in_data, out_data, trace):
		threading.Thread.__init__(self),
		self.thread_id = thread_id
		self.in_data = in_data
		self.out_data = out_data
		self.timeout = 3
		self.iter_count = 0
		self.total_count = len(in_data)
		self.trace = trace

	def select_unprocessed(self):
		with in_mutex:
			try:
				result = self.in_data.pop()
			except:
				result = None
			return result

	def report_progress(self, item):
		global counter
		counter += 1
		print(u"(%d of %d) [%s] %s" % (counter, self.total_count, item['status'], item['url']))

	def process_item(self, item):
		global request_headers
		item['checked'] = int(time.time())

		try:
			response = requests.get(item['url'], timeout = self.timeout, stream = True, headers = request_headers)
			content = response.raw.read(10000, decode_content = True)

			if config.SEARCH_TEXT in content:
				item['status'] = 'blocked'
			else:
				try:
					peer = response.raw._connection.sock.getpeername()
				except:
					item['status'] = 'available'
				else:
					if peer is not None:
						try:
							address = ipaddress.ip_address(peer[0])
						except:
							item['status'] = 'available' # ???
						else:
							if address.is_private:
								item['status'] = 'local-ip'
							else:
								item['status'] = 'available'
					else:
						item['status'] = 'available'
		except Exception as e:
			item['status'] = 'failure'

		with out_mutex:
			if self.trace:
				self.report_progress(item)
			self.out_data.append(item)

		self.iter_count += 1
		if (self.iter_count % 100) == 0:
			gc.collect()

	def set_timeout(self, new_timeout):
		self.timeout = new_timeout

	def run(self):
		while True:
			item = self.select_unprocessed()
			if item is None:
				break
			else:
				self.process_item(item)

# Профилирование
import resource

def signal_handler(signal, frame):
	print("Aborted by signal, exitting.")
	exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGQUIT, signal_handler)

def parse_registry(filename):
	result = []

	tree = etree.parse(filename)	
	records = tree.xpath('//content')
	for item in records:
		try:
			block_type = item.get('blockType', default = 'default')
			decision = item.xpath('decision')[0]
			urls = item.xpath('url')
			ips = item.xpath('ip')
			domains = item.xpath('domain')
			ip_subnets = item.xpath('ipSubnet')

			if block_type == 'default':
				result += [{'url': url.text, 'status': 'unknown', 'reply': None, 'code': 0} for url in urls]
			elif block_type == 'ip':
				pass # NOT IMPLEMENTED
			elif block_type == 'domain':
				result += [{'url': "http://%s/" % domain.text, 'status': 'unknown', 'reply': None, 'code': 0, 'checked': 0} for domain in domains]
			else:
				pass # ???
		except:
			continue

	return result

print("Starting using %d threads" % (config.THREADS,))

try:
	print("Loading dump.xml...")
	in_data = parse_registry('dump.xml')
	out_data = []
except:
	print("dump.xml not found or corrupted. Run rkn-load.py first.")
	exit(-1)

print("Loading succeeded, starting check")

# Инициализируем наши рабочие потоки
threads = {}
for i in range(config.THREADS):
	threads[i] = Worker(i, in_data, out_data, True)
	threads[i].set_timeout(config.HTTP_TIMEOUT)
	threads[i].setDaemon(True)

# Разветвляемся
for index, thread in threads.items():
	thread.start()

# Соединяемся
for index, thread in threads.items():
	thread.join()

# На этом этапе у нас сформирована статистика в массиве out_data, получим данные для внесения в БД
timestamp = int(time.time())
total_count = len(out_data)
available = [i for i in out_data if i['status'] == 'available']
#unavailable = [i for i in out_data if i['status'] in ['blocked', 'failure', 'local-ip']]
available_count = len(available)

# Предварительная оценка ресурсов для записи в лог
stat = resource.getrusage(resource.RUSAGE_SELF)

# Время окончания работы скрипта
execution_end = time.time()
execution_time = execution_end - execution_start
execution_minutes = int(execution_time / 60)
execution_seconds = (execution_time - (execution_minutes * 60))

with open('result.txt', 'w') as f:
	for link in available:
		f.write("%s <%d>\n" % (link['url'], link['checked']))

print("---\nCheck finished in %dm:%.2fs using %d kb RES\nAvailable: %d, not available: %d" % (execution_minutes, execution_seconds, stat.ru_maxrss, available_count, total_count - available_count))
