import telebot
import time
# Для распаралеливания процессов
from threading import Thread
# Для отправки HTTP-запросов и получения данных из Интернета
import requests
# Для обработки и парсинга содержания HTML и XML документов
import bs4
# Для парсинга и работы с HTML/XML документами с использованием библиотеки lxml
from lxml import html
# Загружаем бесплатный неограниченный переводчик https://github.com/nidhaloff/deep-translator
# и импортируем модуль GoogleTranslator из билиотки deep_translator, т.к. только
# этот вариант позволяет не задумываться об api_ley и длинне текста
#!pip install -U deep-translator
from deep_translator import GoogleTranslator
# Для работы с регулярными выражениями
import re
# Для работы со списками
import itertools
# Для создание базы данных из получившихся сведений, для дальнейшей обработки
import pandas as pd
# Для отображения процесса прохода по циклу
from tqdm import tqdm

def get_row(BOX):
  """
  Функция, которая достает сведения из переданного ей элемента.

  Параметры:
  BOX (bs4.element.Tag): элемент из которого надо достать информацию

  Возвращает:
  ROW (dict): словарь с найденной информацией
  """
  main_url = 'https://www.preprints.org'
  # Создаем переменную в которую запишем полученные сведения
  ROW = {}

  # Определим переводчик, который самостоятельно будет определять язык
  # переданного текста и переводить на русский
  translator = GoogleTranslator(source='auto', target='ru')

  # Меняем bs4.element.Tag на lxml.html.HtmlElement
  h = html.fromstring(str(BOX))

  # Достаем название статьи
  name = re.sub(r'^\s|\s{2}|\n', ' ', ''.join(h.xpath('//*[@id="title"]/text()')))
  # Получаем список тем в рамках которых написанна статья, при этом добавляем
  # еще строчку, которая отрабатывается если не были найдены темы. Добавленна
  # т.к. было выясненно что в коде сайта некоторые элементы имеют разные тэги
  subject_list = h.xpath('//*[@href="/search"]/text()')
  subject_list = [i for i in h.xpath('//a[contains(@href, "subject")]/text()') if i !='\n'] if subject_list==[] else subject_list
  # Получаем список ключевых слов связанных с данной статьей
  keyword_list = h.xpath('//a[contains(@href, "keywords")]/text()')
  # Получение краткого описания статьи и заодно отчищаем от лишних пробелов и новых строк
  description = re.sub(r'^\s|\s{2,}|\n]', '', ' '.join(h.xpath('//*[@class="abstract-content"]//text()')))
  # Объединяем название, темы, ключевые слова и описание в один текст,
  # чтобы ускорить процесс перевода на русский язык
  NSKD = '\n'.join([name, ';'.join(subject_list), ';'.join(keyword_list), description])
  # Переводим и снова возвращаем все к разным элементам как было
  NSKD = translator.translate(text = NSKD).split('\n')
  # Записываем все по своим местам
  ROW['Название'] = NSKD[0]
  ROW['Науки'] = [re.sub(r'^\s|\s{2,}|\n]', '', t) for t in NSKD[1].split(';')]
  ROW['Ключевые слова'] = [re.sub(r'^\s|\s{2,}|\n]', '', t) for t in NSKD[2].split(';')]
  ROW['Краткое описание'] = NSKD[3]

  # Прописываем уникальный номер статьи чтобы не дублировать записи при новой загрузке
  ROW['Номер'] = re.sub(r'^\s|\s{2,}|\n]', '', ''.join(h.xpath('//span[@class="content-box-header-element-5"]//text()')))
  # Достаем ссылку на статью и записываем в словарь ROW
  ROW['Ссылка'] = main_url+''.join(h.xpath('//*[@id="title"]/@href'))
  # Достаем всех авторов статьи и записываем в словарь ROW
  ROW['Авторы'] = h.xpath('//*[@class="author-selector"]/text()')
  # Получаем дату публикации статьи и из полученной строчки извлекаем только саму дату
  ROW['Дата публикации'] = re.search(r'\d{1,2} [A-Za-z]+ \d{4}', h.xpath('//*[@class="show-for-large-up"]/*/text()')[0]).group()

  return ROW

def last_message(c):
  if c in ['get', 'g', 'G', '1', 1]:
    last_message = open('last_message.txt', 'r')
    id = last_message.read()
    last_message.flush()
    last_message.close()
    return id
  else:
    last_message = open('last_message.txt', 'w')
    last_message.write(c)
    last_message.flush()
    last_message.close()



def get_df():
  def func(j, i):
    try:
      row = get_row(boxes[i+j])
      results[j].append(row)
    except Exception as error:
      print(error)
      errors[j].append({i+j:error})
  main_url = 'https://www.preprints.org'
  page = 1
  url = f'{main_url}/subject/browse/all?page_num={page}'
  req = requests.get(url)
  print('URL status: ', req.status_code)
  soup = bs4.BeautifulSoup(req.text, "html.parser")
  boxes = soup.find_all('div', {'class':"search-content-box margin-serach-wrapper-left"})

  id_list = [re.sub(r'\n|\s', '', id) for id in html.fromstring(str(soup)).xpath('//*[contains(@class, "element-5")]/a/text()')]
  lid=last_message('G')
  #lid = id_list[2]
  print('last message ID: ', lid)

  lid = id_list.index(lid) if lid in id_list else 100
  if lid == 0:
    print('New posts --- NONE')
    return pd.DataFrame()
  else:
    print('New messages count: ', lid)

    if lid%4==0:
      delemiter = 4
    elif lid%3==0:
      delemiter = 3
    elif lid%2==0:
      delemiter = 2
    else:
      delemiter = 1

    results = {0:[],1:[],2:[],3:[]}
    errors = {0:[],1:[],2:[],3:[]}


    print(f'Get info: {round(lid/delemiter)}/{delemiter}')
    for i in tqdm(range(0, lid, delemiter)):
      th = {}
      for j in range(delemiter):
        th[j] = Thread(target=func, kwargs = {'i':i, 'j':j})
        th[j].start()
        th[j].join()

    print('\nlast message ID: ', id_list[0])
    last_message(id_list[0])
  return pd.DataFrame(list(itertools.chain(*results.values())))