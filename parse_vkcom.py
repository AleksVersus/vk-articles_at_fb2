# данный скрипт парсит все открытые статьи с liveinternet
import sys, os, re, json
import random, datetime
import requests
from bs4 import BeautifulSoup
from bs4 import element as bs_el

def getDate(**args):
	when=datetime.datetime.now()
	args['mode']= (args['mode'] if 'mode' in args else '')
	year = (args['year'] if ('year' in args) else when.year)
	month = (args['month'] if ('month' in args) else when.month)
	day = (args['day'] if ('day' in args) else when.day)
	time = (f"{year}.{month}.{day}" if args['mode']!='xml' else f"{year}-{month}-{day}")
	return time

def parseDate(string):
	print(f'parseDate: {string}')
	# извлекаем дату из статьи 17 окт
	match=re.match(r'(\d+) (\w{3}) в (\d+):(\d+)',string)
	if match!=None:
		month={
			'янв':'01','фев':'02','мар':'03',
			'апр':'04','май':'05','июн':'06',
			'июл':'07','авг':'08','сен':'09',
			'окт':'10','ноя':'11','дек':'12'
		}
		day=fullZero(match.group(1),2)
		return {'day':day, 'month':month[match.group(2)]}
	else:
		return {'day':'01', 'month':'01'}

def fullZero(string,num_lenght,zero='0',dir_='left'):
	string=str(string)
	if dir_=='left':
		return str(zero)*(num_lenght-len(string))+string
	elif dir_=='right':
		return string+str(zero)*(num_lenght-len(string))
	else:
		return string

def imageLoad(image_url,folder_path):
	count=len(os.listdir(folder_path))
	image=requests.get(url)
	with open(folder_path+f'\\image_{fullZero(count,3)}.jpg','wb') as file:
		file.write(image.content)

def getImageLink(alter_links_dict):
	level_list=['w', 'z', 'y', 'x', 'r', 'q', 'p', 'o', 'm', 's']
	for w in level_list:
		if w in alter_links_dict:
			return alter_links_dict[w][0]
			break

class NewSection():
	"""
		NewSection — это класс, который я так назвал для удобства вызова
		Экземпляры данного класса являются своего рода структурными единицами
		того скелета, из которого будет собираться fb2 документ. Секция может
		содержать другие секции или строки (строки представляют собой непосредственно
		элементы bs4)
	"""
	def __init__(self, source, **args):
		self.source=(source if type(source)==list else [source]) # исходный набор строк
		self.sections=[] # вложенные секции
		self.body=[] # вложенные строки
		self.title="" # заголовок секции
		self.title_id="" # идентификатор секции
		self.date_time="" # дата, когда написана или опубликована статья
		# сразу назначаем title_id и title, если они переданы
		self.title_id=(args['title_id'] if "title_id" in args else "")
		self.title=(args['title']if "title" in args else "")
		# после того, как задали все свойства, конвертим исходник с помощью встроенных функций
		self.sourceConvert(self.source)
	def sourceToBody(self, set_strings):
		self.body=set_strings
	def sourceConvert(self, set_strings):
		# функция принимает на вход набор строк
		# получаем верхний уровень заголовков и упоминания
		top_level_head, levels_count = self.getTopLevel(set_strings)
		#print(f"Source Convert [0]: get top level of head = {top_level_head}")
		if top_level_head!="":
			# заголовок верхнего уровня существует
			#print(f"Source Convert [1]: top level head is exist.")
			if levels_count[top_level_head][0]==1 and levels_count[top_level_head][1]==0:
				# он один и он в верхней строке секции
				#print(f"Source Convert [2]: top level head is one and top.")
				self.title=set_strings[0].text
				self.title_id=set_strings[0].find('span',{'class':'article_anchor_button'})['id']
				set_strings=set_strings[1:] # режем набор строк с первого элемента, так как нулевой обработан
				# получаем верхний уровень заголовков и упоминания
				top_level_head, levels_count = self.getTopLevel(set_strings)
				#print(f"Source Convert [3]: get top level ={top_level_head} set.lenght={len(set_strings)}.")
				if top_level_head!="":
					# заголовок верхнего уровня существует
					#print(f"Source Convert [4]: top level head is exist. Split other strings.")
					# пытаемся разбить оставшиеся строки
					self.split(set_strings)
				else:
					# заголовок верхнего уровня не существует, все строки помещаются в body
					#print(f"Source Convert [5]: top level head is not exist. Add strings to body.")
					self.sourceToBody(set_strings)
			else:
				# такой заголовок не один, либо не в верхней строке, значит секцию нужно разбить на подсекции
				self.title=""
				self.title_id=self.rndID(mode='first-letter')
				#print(f"Source Convert [6]: top level head is not one or top. Split all strings. {self.title_id}")
				self.split(set_strings)
		else:
			# в наборе не найдены заголовки, значит весь набор становится телом секции
			# не забываем про айдишник
			self.title=""
			self.title_id=self.rndID(mode='first-letter')
			#print(f"Source Convert [7]: top level head is not exist. All Strings to body. {self.title_id}")
			self.sourceToBody(set_strings)
	def split(self, set_strings):
		# на данном этапе у нас уже должен быть set_strings - набор элементов (строк) bs4
		# получаем заголовок верхнего уровня, и сколько раз и какие заголовки встречались в списке строк
		top_level_head, levels_count = self.getTopLevel(set_strings)
		string_list=[] # сюда набираем строки (набор)
		section=None # временное хранилище секции
		#print(f"Split [0]: top_level_head={top_level_head} set.lenght={len(set_strings)}")
		# перебираем теги
		for tag in set_strings:
			if "article__info_line" in tag['class']:
				# в информацию о книге
				for el in tag.contents:
					if type(el)==bs_el.Tag:
						el.decompose()
					else:
						self.date_time=el.text
				# print("article__info_line")
			elif tag.name==top_level_head:
				#print(f"Split [1]: tag.name={tag.name} tag.text={tag.text}")
				if len(string_list)>0:
					#print(f"Split [2]: create NewSection from {len(string_list)} strings.")
					self.sections.append(NewSection(string_list))
					string_list=[]
				#print(f"Split [3]: Add tag '{tag.name}' to new set.")
				string_list.append(tag)
			else:
				#print(f"Split [4]: Add tag '{tag.name}' to new set.")
				string_list.append(tag)
		if len(string_list)>0:
			#print(f"Split [5]: create NewSection from {len(string_list)} strings.")
			self.sections.append(NewSection(string_list))
	def getFB2(self):
		text=""
		text+=f'<section id="avs-{self.title_id}">\n'
		if self.title!="": text+=f'<title><p>{self.title}</p></title>'
		if len(self.sections)!=0:
			for i in self.sections:
				text+=i.getFB2()
		elif len(self.body)!=0:
			for tag in self.body:
				text+=self.convertTag(tag)
		else:
			text+='  <empty-line/>\n'
		text+="\n</section>\n"
		return text
	def getTopLevel(self, set_strings):
		# на вход принимаем набор строк
		# заголовок верхнего уровня и максимальный уровен
		top_level_head, tag_lev = str(""), int(9)
		# здесь считаем, сколько заголовков каждого типа у нас встретилось и на какой строке был встречен такой заголовок впервые
		levels_count={'h1':[0,-1], 'h2':[0,-1], 'h3':[0,-1], 'h4':[0,-1], 'h5':[0,-1], 'h6':[0,-1]}
		# требуется найти заголовок верхнего уровня, для этого перебираем список
		for index, tag in enumerate(set_strings):
			if tag.name in ('h1','h2','h3','h4','h5','h6'):
				levels_count[tag.name][0]+=1
				if levels_count[tag.name][1]==-1: levels_count[tag.name][1]=index
				if tag_lev>int(tag.name[1:]):
					tag_lev=int(tag.name[1:])
					top_level_head=tag.name
		# возвращаем tagname заголовка верхнего уровня и сколько он раз встречается и где.
		return top_level_head, levels_count
	def convertTag(self, tag):
		text=""
		if tag.name=='p':
			text+="<p>"
			for el in tag.contents:
				if type(el)==bs_el.Tag:
					text+=self.convertTag(el)
				else:
					text+=el.text
			text+="</p>\n"
		if tag.name=='em':
			text+="<emphasis>\n"
			for el in tag.contents:
				if type(el)==bs_el.Tag:
					text+=self.convertTag(el)
				else:
					text+=el.text
			text+="\n</emphasis>\n"
		if tag.name=='strong':
			text+="<strong>\n"
			for el in tag.contents:
				if type(el)==bs_el.Tag:
					text+=self.convertTag(el)
				else:
					text+=el.text
			text+="\n</strong>\n"
		if tag.name=='figure':
			images=tag.find_all('img')
			alter_links=tag.find('div',{'class':'article_object_sizer_wrap'})
			if alter_links!=None:
				alter_links_dict=json.loads(alter_links['data-sizes'].replace(r'\/','/'))[0]
				new_link=getImageLink(alter_links_dict)
				print(new_link)
				#imageLoad(new_link,'.\\images')
			else:
				new_link=None
			for i in images:
				if new_link!=None: i['src']=new_link
				text+=f'<p><a l:href="{i["src"].replace("&","&amp;")}">{i["alt"]}</a></p>\n'
			iframes=tag.find_all('iframe')
			for i in iframes:
				text+=f'<p><a l:href="{i["src"].replace("&","&amp;")}">Видео</a></p>\n'
			text+=f'<p><emphasis>{tag.figcaption.text}</emphasis></p>\n'
		if tag.name=='a':
			text+=f'<a l:href="{tag["href"]}">'
			for el in tag.contents:
				if type(el)==bs_el.Tag:
					text+=self.convertTag(el)
				else:
					text+=el.text
			text+='</a>'
		return text
	def rndID(self, **args):
		args['mode']=(args['mode'] if 'mode' in args else '')
		letters="0123456789ABCDEF"
		x = (10 if args['mode']=='first-letter' else 0)
		result = ''.join(random.choice(letters[x:]) for i in range(8))+'-'
		result += ''.join(random.choice(letters) for i in range(4))+'-'
		result += ''.join(random.choice(letters) for i in range(4))+'-'
		result += ''.join(random.choice(letters) for i in range(4))+'-'
		result += ''.join(random.choice(letters) for i in range(12))
		return result

def getArticle(url):
	text=""
	page=""
	file_name=url.split('@')[1]
	if '?' in file_name: file_name=file_name.split('?')[0]
	# print(file_name)
	# извлекаем страницу. Данный кусочек нужен, чтобы не делать к серверу миллион запросов, если возникнет ошибка
	# а работать с уже скачанной страницей
	if os.path.isfile(f'.\\images\\{file_name}.html'):
		print('Из файла')
		with open(f'.\\images\\{file_name}.html','r',encoding='utf-8') as file:
			page=file.read()
	else:
		print('Загружаем с сайта')
		page=requests.get(url).text
		with open(f'.\\images\\{file_name}.html','w',encoding='utf-8') as file:
			file.write(page)

	soup=BeautifulSoup(page,"html.parser")
	body=soup.body
	article=body.select('div[class~="article_view"]')[0]

	# -------------------- информация о книге -------------------------
	author=body.find('div',{'class':'articleView__ownerName'}).text
	# -------------------- информация о книге -------------------------
	fb2_sections=NewSection(article.contents)
	fb2output=fb2_sections.getFB2()
	fb2_export_text=""
	header=fb2_sections.title
	date_time=fb2_sections.date_time
	month_day=parseDate(date_time)
	date_xml=getDate(mode='xml',month=month_day['month'],day=month_day['day'])
	book_id=fb2_sections.rndID()

	fb2_export_text+=f'<?xml version="1.0" encoding="utf-8"?>\n'
	fb2_export_text+=f'<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" xmlns:l="http://www.w3.org/1999/xlink">\n'
	fb2_export_text+=f' <description>\n'
	fb2_export_text+=f'  <title-info>\n'
	fb2_export_text+=f'   <genre>nonf_publicism</genre>\n<genre>nonf_criticism</genre>\n'
	fb2_export_text+=f'   <author>'
	fb2_export_text+=f'    <first-name>{author}</first-name>\n'
	fb2_export_text+=f'    <last-name></last-name>\n'
	fb2_export_text+=f'   </author>\n'
	fb2_export_text+=f'   <book-title>{header}</book-title>\n'
	fb2_export_text+=f'   <annotation><p>Данный файл был автоматически сгенерирован скриптом из статьи на сайте vk.com, размещённой по адресу <a l:href="{url}">{url}</a>.</p></annotation>\n'
	fb2_export_text+=f'   <date value="{date_xml}">{date_time}</date>\n'
	fb2_export_text+=f'   <lang>ru</lang>\n'
	fb2_export_text+=f'  </title-info>\n'
	fb2_export_text+=f'  <document-info>\n'
	fb2_export_text+=f'   <genre>nonf_publicism</genre>\n<genre>nonf_criticism</genre>\n'
	fb2_export_text+=f'   <author>\n'
	fb2_export_text+=f'    <first-name>{author}</first-name>\n'
	fb2_export_text+=f'    <last-name></last-name>\n'
	fb2_export_text+=f'   </author>\n'
	fb2_export_text+=f'   <program-used>vk-articles-conv-to-fb2.py</program-used>\n'
	fb2_export_text+=f'   <date value="{date_xml}">{date_time}</date>\n'
	fb2_export_text+=f'   <id>{book_id}</id>\n'
	fb2_export_text+=f'   <version>1.1</version>\n'
	fb2_export_text+=f'   <history><p>Сгенерировано скриптом. Aleks Versus by</p></history>\n'
	fb2_export_text+=f'  </document-info>\n'
	fb2_export_text+=f' </description>\n'
	fb2_export_text+=f' <body>{fb2output}</body>\n'
	fb2_export_text+=f'</FictionBook>\n'
		
	# print(f"Автор: {author}\nЗаголовок: {header}\nИдентификатор заголовка: {header_id}")

	with open(f'.\\articles\\{file_name}.fb2','w',encoding='utf-8') as file:
		file.write(fb2_export_text)

def main(url_or_list):
	if type(url_or_list)==str:
		# если мы передаём не список адресов, а один адрес, значит нужно получить список адресов
		page=requests.get(url_or_list).text # запрашиваем страницу со списком статей
		# готовим суп
		soup=BeautifulSoup(page,"html.parser")
		body=soup.body
		articles_links=body.find_all('a',{'class':'author-page-article__href'})
		url_or_list=[]
		for link in articles_links:
			if re.match(r'https://vk\.com',link['href'])==None:
				url_or_list.append('https://vk.com'+link['href'])
			else:
				url_or_list.append(link['href'])
	for url in url_or_list:
		getArticle(url)

if __name__=="__main__":
	url_or_list=[f"https://vk.com/@flab20-socialnye-seti-kak-nepodemnyi-gruz"]
	main(url_or_list)
