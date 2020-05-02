import os.path, ssl, psycopg2, json, requests, random, re, io
import urllib.parse
from aiohttp import web
from time import sleep
from pprint import pprint
from collections import namedtuple

#edit_edition

class Log:
	def write(self, text):
		print(text)

class Configure:
	config_file = 'pepaka9001.cfg'
	telegram_token = None
	telegram_url = None
	ssl_fullchain = None
	ssl_privkey = None
	webhook_listen = None
	webhook_port = None
	db_ip = None
	db_name = None
	db_user = None
	db_password = None
	db_connection = None
	ssl_context = None

	def load(self):
		cfg = {}
		if os.path.exists(self.config_file):
			file = open(self.config_file, 'tr')
			for line in file.readlines():
				key_value = (line.rstrip()).split('=')
				cfg[key_value[0]] = key_value[1]
		else:
			print('Please create config file')
			exit()

		self.telegram_token = cfg.get('telegram_token')
		self.telegram_url = cfg.get('telegram_url') + self.telegram_token
		self.ssl_fullchain = cfg.get('ssl_fullchain')
		self.ssl_privkey = cfg.get('ssl_privkey')
		self.webhook_listen = cfg.get('webhook_listen')
		self.webhook_port = cfg.get('webhook_port')
		self.db_ip = cfg.get('db_ip')
		self.db_name = cfg.get('db_name')
		self.db_user = cfg.get('db_user')
		self.db_password = cfg.get('db_password')

	def connect_to_db(self):
		self.db_connection = psycopg2.connect(dbname=self.db_name, user=self.db_user, password=self.db_password, host=self.db_ip)
	
	def webhook_setup(self):
		self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
		self.ssl_context.load_cert_chain(self.ssl_fullchain, self.ssl_privkey)

class Webhook:
	async def start(request):
		#Приходит вебхук и начинается конвертить жсон в словари
		response = await request.text()
		print('------------------------------------')
		response = response.replace('from', 'fromm')
		json_data = json.loads(response)

		if json_data.get('message'):
			json_data = json_data['message']
		elif json_data.get('edited_message'):
			print('Edited message')
			json_data = json_data['edited_message']
		else:
			print('Not supported JSON data:', json_data)
		#а тут начинается переборка всех элементов, что есть
		global message
		message = Message()
		for key, val in json_data.items():
			Collector(key, val)		
		CheckAction()
		
			

		
		return web.Response()
	app = web.Application()
	app.add_routes([web.post('/', start), web.post('/{name}', start)])


class Message:
	def __init__(self):
		self.message_id = None
		self.user_id = None
		self.first_name = None
		self.last_name = None
		self.full_name = None
		self.chat_id = None
		self.text = None
		self.command = None
		self.sticker = None
		self.reply_message_id = None
		self.reply_text = None
		self.reply_user_id = None

class Collector():
	def __init__(self, method, data):
		method = '_' + method
		try:
			method = getattr(self, method)
			method(data)
		except Exception:
			print('No handler', method)


	def _message_id(self, data):
		message.message_id = data
		print('_message_id:', message.message_id)

	def _fromm(self, data):
		message.user_id = data['id']
		message.first_name = data['first_name']
		try:
			message.last_name = data['last_name']
			message.full_name = message.first_name + ' ' + message.last_name
		except:
			message.full_name = message.first_name

		print('_fromm:', message.full_name)

	def _chat(self, data):
		message.chat_id = data['id']
		print('_chat:', message.chat_id)

	def _text(self, data):
		message.text = data
		print('_text:', message.text)

	def _reply_to_message(self, data):
		print(data)
		message.reply_message_id = data['message_id']
		message.reply_user_id = data['fromm']['id']
		message.reply_text = data['text']
		try:
			message.reply_text = data['text']
		except:
			print('No text in reply')

	def _sticker(self, data):
		message.sticker = data['set_name']
		print('_sticker:', message.sticker)


class Methods:
	def http_get(self, url):
		#print(url)
		r = requests.get(url)
		#print('http_get:', r)

	def sendChatAction(self, type):
		url = cfg.telegram_url + '/sendChatAction?chat_id=' + str(message.chat_id) + '&action=' + type
		self.http_get(url)
		sleep(random.random())

	def sendMessage(self, text):
		url = cfg.telegram_url + '/sendMessage?chat_id=' + str(message.chat_id) + '&parse_mode=HTML&text=' + str(text)
		self.http_get(url)

	def replyMessage(self, text, id):
		url = cfg.telegram_url + '/sendMessage?chat_id=' + str(message.chat_id) + '&parse_mode=HTML&reply_to_message_id=' + str(id) + '&text=' + str(text)
		self.http_get(url)

	def deleteMessage(self, message_id):
		url = cfg.telegram_url + '/deleteMessage?chat_id=' + str(message.chat_id) + '&message_id=' + str(message_id)
		self.http_get(url)

	def getStickerSet(self):
		url = cfg.telegram_url + '/getStickerSet?name=' +str(message.sticker)
		self.http_get(url)

	def sendSticker(self, sticker):
		url = cfg.telegram_url + '/sendSticker?chat_id=' + str(message.chat_id) + '&sticker=' + str(sticker)
		self.http_get(url)

class CheckAction:
	def __init__(self):
		if(message.text):
			its_command = False
			message.command = message.text.lower()

			if message.reply_user_id == 384644516:#@pepakabot
				its_command = True
				Talk()

			if message.command == '!бд' and message.user_id == 111304154: #@bazinga09
				its_command = True
				print('BD report')
				DB().get_info()

			if message.command.startswith('пепяк') and 'или' in message.command:
				its_command = True
				ToBeOrNoToBe()

			if 'пепяк' in message.command and not its_command:
				its_command = True
				Talk()

			if message.command == '/help' or message.command == '/help@pepakabot':
				its_command = True
				Help()

			if message.command.startswith('/me') or message.command.startswith('!мну'):
				its_command = True
				Mnu()

			if message.command.startswith('!d'):
				its_command = True
				Dice()

			if message.command.startswith('!онимэ'):
				its_command = True
				Picts('http://anime.reactor.cc',
								'src="http://img10.reactor.cc/pics/post')

			if message.command.startswith('!оппаи'):
				its_command = True
				Picts('http://anime.reactor.cc/tag/Oppai',
								'src="http://img10.reactor.cc/pics/post')

			if message.command.startswith('!сиськи'):
				its_command = True
				Picts('http://joyreactor.cc/tag/%D0%A1%D0%B8%D1%81%D1%8C%D0%BA%D0%B8',
								'src="http://img10.joyreactor.cc/pics/post')

			if message.command.startswith('!жопки'):
				its_command = True
				Picts('http://joyreactor.cc/tag/%D0%BF%D0%BE%D0%BF%D0%B0',
								'src="http://img10.joyreactor.cc/pics/post')

			if message.command.startswith('!wh'):
				its_command = True
				Picts('http://wh.reactor.cc',
								'src="http://img1.reactor.cc/pics/post')

			if message.command.startswith('!котэ') or message.command.startswith('!котик'):
				its_command = True
				Picts('http://joyreactor.cc/tag/%D0%BA%D0%BE%D1%82%D1%8D',
								'src="http://img0.joyreactor.cc/pics/post')

			if message.command.startswith('!манул') or message.command.startswith('!марго'):
				its_command = True
				Picts('http://joyreactor.cc/tag/%D0%BC%D0%B0%D0%BD%D1%83%D0%BB',
								'src="http://img1.joyreactor.cc/pics/post')


			if not its_command:
				print('not command')
				DB().write_msg()

		if message.sticker:
			Stickers()


		if message.reply_message_id:
			#its_command = False
			if(message.text == '!') and message.reply_text and message.reply_user_id != 384644516:
				Huebot()



class DB:
	def write_msg(self):
		cfg.db_cursor = cfg.db_connection.cursor()
		m = cfg.db_cursor.execute('SELECT message FROM messages WHERE message=%s LIMIT 1;', (message.text,))
		m = cfg.db_cursor.fetchall()
		if not m:
			print('UNIQ')
			cfg.db_cursor.execute('INSERT INTO messages (message) VALUES (%s)', (message.text,))
			cfg.db_connection.commit()
		else:
			print('NOT UNIQ')

	def get_info(self):
		cfg.db_cursor = cfg.db_connection.cursor()
		m = cfg.db_cursor.execute('SELECT count(*) FROM messages;')
		m = cfg.db_cursor.fetchall()
		m = m[0][0]
		s = cfg.db_cursor.execute('SELECT count(*) FROM stickers;')
		s = cfg.db_cursor.fetchall()
		s = s[0][0]
		text = 'В пепячьей базе на данный момент обнаружено <b>' + str(m) + '</b> сообщений и <b>' + str(s) + '</b> стикеров.'
		methods.sendChatAction('typing')
		methods.sendMessage(text)

class Stickers:
	def __init__(self):
		cfg.db_cursor = cfg.db_connection.cursor()
		cfg.db_cursor.execute('SELECT name FROM stickers WHERE name= %s;', (message.sticker,))
		sticker = cfg.db_cursor.fetchall()
		if not sticker:
			print('I need this sticker')
			url = cfg.telegram_url + '/getStickerSet?name=' +str(message.sticker)
			r = requests.get(url)
			json_sticker_pack = r.json()
			json_sticker_pack = json_sticker_pack['result']['stickers']
			for el in json_sticker_pack:
				print(el['file_id'])
				cfg.db_cursor.execute('INSERT INTO stickers (name, sticker_id) VALUES (%s, %s)', (message.sticker, el['file_id']))

			cfg.db_connection.commit()
		else:
			print('I do not need this sticker')

class Talk:
	def __init__(self):
		print('start small talk')
		if random.randint(0,1) == 0:
			print('send sticker')
			cfg.db_cursor = cfg.db_connection.cursor()
			cfg.db_cursor.execute('SELECT sticker_id FROM stickers ORDER BY RANDOM() LIMIT 1;')
			sticker = cfg.db_cursor.fetchall()
			print(sticker[0][0])
			methods.sendSticker(sticker[0][0])
		else:
			print('send text')
			cfg.db_cursor = cfg.db_connection.cursor()
			cfg.db_cursor.execute('SELECT message FROM messages ORDER BY RANDOM() LIMIT 1;')
			text = cfg.db_cursor.fetchall()
			print(text[0][0])
			methods.sendChatAction('typing')
			methods.replyMessage(text[0][0], message.message_id)

class Help:
	def __init__(self):
		help_text = 'Чаво я умею:\r\n\r\n<b>/me</b> или <b>!мну</b> - обозначить действие.\r\n\r\n' + \
						'<b>!d1-999</b> - бросить кубик с указанным количеством граней.\r\n\r\n' + \
						'Помогу с выбором, если ко мне обратиться по имени и перечислить варианты через "или".\r\n' + \
						'Например:\r\n<b>"Пепяка, есть или спать?</b>"\r\n\r\n' + \
						'Прочие команды:\r\n' + \
						'<b>!сиськи</b>\r\n' + \
						'<b>!жопки</b>\r\n' + \
						'<b>!онимэ</b>\r\n' + \
						'<b>!оппаи</b>\r\n' + \
						'<b>!котик</b>\r\n\r\n' + \
						'А ещё я немного хуебот'
		methods.sendChatAction('typing')
		methods.sendMessage(help_text)

class Mnu:
	def __init__(self):
		if message.command.startswith('/me'):
			mnu_text = message.command[4:]
		else:
			mnu_text = message.command[5:]
		methods.deleteMessage(int(message.message_id))
		methods.sendMessage('<b>* ' + str(message.full_name) + '</b> ' + mnu_text)

class ToBeOrNoToBe:
	def __init__(self):
			def del_trash(text):
				return (re.sub('\W+','', text ))
			word_list = message.text.split()
			answer_list = []
			temp = ''

			for word in word_list:
				if 'пепяк' not in word.lower() and word.lower() != 'или':
					temp += del_trash(word) + ' '
				elif temp != '':
					answer_list.append(temp)
					temp = ''

			answer_list.append(temp)
			answer = random.choice(answer_list)
			#print(answer)
			#print(message.reply_message_id)
			methods.sendChatAction('typing')
			methods.replyMessage(answer, message.reply_message_id)

class Dice:
	def __init__(self):
		try:
			num = int(message.command[2:])
			if num > 0:
				methods.deleteMessage(int(message.message_id))
				rnd = random.randint(1, num)
				log.write('random number is ' + str(rnd))
				methods.sendChatAction('typing')				
				methods.sendMessage('<b>' + message.full_name + '</b> выбросил <b>' + str(rnd) + ' из ' + message.command[2:] + '</b>.')
				
				if rnd == 1:					
					methods.sendChatAction('typing')
					methods.sendMessage('Ха-ха! Етить ты маубедитель!')

			else:				
				methods.sendChatAction('typing')				
				methods.sendMessage('Кажется я проглотил твой кубик, <b>' + message.full_name + '</b>.')

		except:
			methods.sendChatAction('typing')				
			methods.sendMessage('<b>' + message.full_name + '</b> зашвырнул кубик за грань реальности.')

class Huebot:
	def __init__(self):
		vowels = ('а', 'е', 'ё', 'и', 'о', 'у', 'ы', 'э', 'ю', 'я')
		reg = re.compile('[^а-яА-ЯёЁ -]')
		text = reg.sub('', message.reply_text)

		try:
			if text:
				word = text.rsplit(' ', 1)[-1]
				print(word)
				count = 0
				it_vowel = False
				while not it_vowel:
					if word[count] in vowels:
						it_vowel = True
						break
					else:
						count += 1
				hue_array ={
							'а':'хуя',
							'е':'хуе',
							'ё':'хуё',
							'и':'хуи',
							'о':'хуё',
							'у':'хую',
							'ы':'хуи',
							'э':'хуэ',
							'ю':'хую',
							'я':'хуя'}			

				hue_text = hue_array[word[count]] + word[count + 1:]
				hue_text = hue_text.title() + '!'
				print(hue_text)
				methods.deleteMessage(message.message_id)
				methods.sendChatAction('typing')
				methods.replyMessage(hue_text, message.reply_message_id)
		except:
			print('хуергу мне шлют!')



class Picts:	
	def __init__(self, url, pattern):
		print(url)
		template ='''pagination_expanded"><span class='current'>\d+'''
		r = requests.get(url)
		reg = re.search(template, r.text)
		page = random.randint(1, int(reg.group(0)[43:]))
		url = url + '/' + str(page)
		methods.sendChatAction('upload_photo')
		sleep(1)
		r = requests.get(url)
		html = str(r.text).split()
		urls = []
		for line in html:
			if pattern in line:
				img_url = line.replace('src=', '')
				img_url = img_url.replace('"', '')
				if img_url.endswith('jpg') or img_url.endswith('jpeg') or img_url.endswith('gif') or img_url.endswith('png'):
					urls.append(img_url)
		rnd_img = urls[random.randint(0, len(urls) - 1)]
		print(rnd_img)
		rnd_image_name = str(rnd_img.split('/')[-1:])
		rnd_image_name = rnd_image_name[2:-2]
		log.write(urllib.parse.unquote(rnd_image_name))
		sleep(1)
		headers = {'Referer': url}
		remote_image = requests.get(rnd_img, headers = headers)
		out = open(urllib.parse.unquote(rnd_image_name), 'wb')
		out.write(remote_image.content)
		out.close()
		photo = io.BytesIO(remote_image.content)
		photo.name = rnd_image_name
		if rnd_img.endswith('mp4'):
			log.write('MP4')
			files = {'video': photo}
			temp_url = cfg.telegram_url + '/sendVideo'
		if rnd_img.endswith('webm') or rnd_img.endswith('gif'):
			files = {'document': photo}
			temp_url = cfg.telegram_url + '/sendDocument'
		else:
			files = {'photo': photo}
			temp_url = cfg.telegram_url + '/sendPhoto'
		data = {'chat_id': message.chat_id}
		
		r = requests.post(temp_url, files = files, data = data)
		print(r)



log = Log()
log.write('Start Pepaka system 9001')

cfg = Configure()
cfg.load()
cfg.connect_to_db()
cfg.webhook_setup()

webhook = Webhook()
methods = Methods()
web.run_app(webhook.app, host=cfg.webhook_listen, port=cfg.webhook_port, ssl_context=cfg.ssl_context)

