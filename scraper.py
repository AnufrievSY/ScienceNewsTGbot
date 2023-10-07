# Для распараллеливания процессов
from threading import Thread
# Для отправки HTTP-запросов и получения данных из Интернета
import requests
# Для обработки и парсинга содержания HTML и XML документов
import bs4
# Для парсинга и работы с HTML/XML документами с использованием библиотеки lxml
from lxml import html
# Загружаем бесплатный неограниченный переводчик https://github.com/nidhaloff/deep-translator
# и импортируем модуль GoogleTranslator из библиотеки deep_translator, т.к. только
# этот вариант позволяет не задумываться об api_ley и длинне текста
from deep_translator import GoogleTranslator
# Для работы с регулярными выражениями
import re
# Для работы со списками
import itertools
# Для создания базы данных из получившихся сведений, для дальнейшей обработки
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
    # Получаем список тем в рамках которых написана статья. При этом добавляем
    # еще строчку, которая отрабатывается если не были найдены темы.
    subject_list = h.xpath('//*[@href="/search"]/text()')
    subject_list = [i for i in h.xpath('//a[contains(@href, "subject")]/text()') if
                    i != '\n'] if subject_list == [] else subject_list
    # Получаем список ключевых слов связанных с данной статьей
    keyword_list = h.xpath('//a[contains(@href, "keywords")]/text()')
    # Получение краткого описания статьи и заодно отчищаем от лишних пробелов и новых строк
    description = re.sub(r'^\s|\s{2,}|\n]', '', ' '.join(h.xpath('//*[@class="abstract-content"]//text()')))
    # Объединяем название, темы, ключевые слова и описание в один текст,
    # чтобы ускорить процесс перевода на русский язык
    NSKD = '\n'.join([name, ';'.join(subject_list), ';'.join(keyword_list), description])
    # Переводим и снова возвращаем все к разным элементам как было
    NSKD = translator.translate(text=NSKD).split('\n')
    # Записываем все по своим местам
    ROW['Название'] = NSKD[0]
    ROW['Науки'] = [re.sub(r'^\s|\s{2,}|\n]', '', t) for t in NSKD[1].split(';')]
    ROW['Ключевые слова'] = [re.sub(r'^\s|\s{2,}|\n]', '', t) for t in NSKD[2].split(';')]
    ROW['Краткое описание'] = NSKD[3]

    # Прописываем уникальный номер статьи чтобы не дублировать записи при новой загрузке
    ROW['Номер'] = re.sub(r'^\s|\s{2,}|\n]', '',
                          ''.join(h.xpath('//span[@class="content-box-header-element-5"]//text()')))
    # Достаем ссылку на статью и записываем в словарь ROW
    ROW['Ссылка'] = main_url + ''.join(h.xpath('//*[@id="title"]/@href'))
    # Достаем всех авторов статьи и записываем в словарь ROW
    ROW['Авторы'] = h.xpath('//*[@class="author-selector"]/text()')
    # Получаем дату публикации статьи и из полученной строчки извлекаем только саму дату
    ROW['Дата публикации'] = re.search(r'\d{1,2} [A-Za-z]+ \d{4}',
                                       h.xpath('//*[@class="show-for-large-up"]/*/text()')[0]).group()

    return ROW


def last_message(c=None):
    """
    Функция, которая возвращает ID последней высланной новости.
    Если изменено значение по умолчанию, то записывает новый ID.
    """
    if c:
        last_news_id_file = open('last_message.txt', 'w')
        last_news_id_file.write(c)
        last_news_id_file.flush()
        last_news_id_file.close()
    else:
        last_news_id_file = open('last_message.txt', 'r')
        last_id = last_news_id_file.read()
        last_news_id_file.flush()
        last_news_id_file.close()
        return last_id


def get_df():
    def func(batch_number, record_number):
        """
        Функция для Thread.
        Если возникает любая ошибка, то выводит ее текст и номер записи,
            в которой возникла эта ошибка.

        Параметры:
        batch_number (int): номер потока, используется для записи результата в свою ячейку словаря;
        record_number (int): номер записи в потоке, суммируется с batch_number для получения записи.
        """
        try:
            row = get_row(boxes[batch_number + record_number])
            results[batch_number].append(row)
        except Exception as error:
            print(f'{batch_number + record_number}: {error}')

    # Прописываем главную ссылку сайт
    main_url = 'https://www.preprints.org'
    # Прописываем ссылку с которой будем брать информацию
    url = f'{main_url}/subject/browse/all?page_num=1'
    # Отправляем запрос на получение информации с переданной ссылки
    req = requests.get(url)
    # Выводим статус запроса, если все хорошо - 200
    print('URL status: ', req.status_code)
    # Превращаем все в удобный формат для извлечения данных
    soup = bs4.BeautifulSoup(req.text, "html.parser")
    # Получаем список элементов - статей.
    boxes = soup.find_all('div', {'class': "search-content-box margin-serach-wrapper-left"})
    # Получаем список из ID новостей, отчистив их от лишних пробелов и новых строк
    id_list = [re.sub(r'\n|\s', '', news_id) for news_id in
               html.fromstring(str(soup)).xpath('//*[contains(@class, "element-5")]/a/text()')]
    # Получаем ID последней отправленной новости из файла last_message.txt
    lid = last_message()
    # Выводим ID последней отправленной новости
    print('last message ID: ', lid)
    # Если последний ID есть в списке id_list, то мы прописываем его индекса,
    #   чтобы цикл не проходился по всем новостям, а получил только новые записи.
    # Если же последнего ID нет в списке, значит мы достаем все новости со страницы.
    lid = id_list.index(lid) if lid in id_list else 100
    # Если же последний отправленный ID совпадает с первой записью на странице,
    #   значит на сайте не было новых записей и мы возвращаем пустой датафрейм.
    if lid == 0:
        print('New posts --- NONE')
        return pd.DataFrame()
    else:
        # Выводим количество новых записей.
        print('New messages count: ', lid)
        # Определяем разделитель - количество паралельных потоков, которые будут запущены.
        # Был использован именно такой вариант, т.к. через него была реализованна приоритетность
        #   наибольшего количества поток, для ускорения работы.
        delimiter = 4 if lid % 4 == 0 else 3 if lid % 3 == 0 else 2 if lid % 2 == 0 else 1
        # Создаем словарь, в который будут записываться результаты работы потоков.
        results = {0: [], 1: [], 2: [], 3: []}
        # Выводим информацию о том, сколько потоков будет запущено и сколько будет записей
        # в каждом потоке.
        print(f'Get info: {delimiter}/{round(lid / delimiter)}')
        # Запускаем цикл с отображением прогресса выполнения.
        for i in tqdm(range(0, lid, delimiter)):
            # Запускаем потоки.
            th = {}
            for j in range(delimiter):
                th[j] = Thread(target=func, kwargs={'record_number': i, 'batch_number': j})
                th[j].start()
                th[j].join()
        # Выводим номер последней записи.
        print('\nlast message ID: ', id_list[0])
        # Добавляем номер последней записи в last_message.txt
        last_message(id_list[0])

    return pd.DataFrame(list(itertools.chain(*results.values())))
