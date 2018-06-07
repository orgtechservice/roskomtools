
# Сторонние пакеты
from lxml import etree

def parse_registry(filename, database):
	cursor = database.cursor()

	# Очистим таблицы
	cursor.execute("DELETE FROM urls")
	cursor.execute("DELETE FROM domains")
	cursor.execute("DELETE FROM ips")
	cursor.execute("DELETE FROM subnets")
	cursor.execute("DELETE FROM content")

	# Заполним их заново
	tree = etree.parse(filename)	
	records = tree.xpath('//content')
	for item in records:
		try:
			content_id = str(item.get('id', default = '0'))
			block_type = item.get('blockType', default = 'default')
			#decision = item.xpath('decision')[0]

			cursor.execute("INSERT INTO content (content_id, content_block_type) VALUES (?, ?)", (content_id, block_type))

			if block_type == 'default':
				for url in item.xpath('url'):
					cursor.execute("INSERT INTO urls (url_content_id, url_text) VALUES (?, ?)", (content_id, url.text))
				for domain in item.xpath('domain'):
					cursor.execute("INSERT INTO domains (domain_content_id, domain_text) VALUES (?, ?)", (content_id, domain.text))
			elif block_type == 'ip':
				for ip in item.xpath('ip'):
					cursor.execute("INSERT INTO ips (ip_content_id, ip_text) VALUES (?, ?)", (content_id, ip.text))
				for subnet in item.xpath('ipSubnet'):
					cursor.execute("INSERT INTO subnets (subnet_content_id, subnet_text) VALUES (?, ?)", (content_id, subnet.text))
			elif block_type == 'domain':
				for domain in item.xpath('domain'):
					cursor.execute("INSERT INTO domains (domain_content_id, domain_text) VALUES (?, ?)", (content_id, domain.text))
			else:
				pass # ???
		except:
			continue

	cursor.close()
	database.commit()
