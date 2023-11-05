import requests
import bs4
from lxml import html
from tqdm import tqdm
import json
import settings


class subject_dict():
    def update():
        main_url = 'https://www.preprints.org'
        req = requests.get(main_url)
        print(f'status | subject_dict.update | {req.status_code}')
        soup = bs4.BeautifulSoup(req.text, "html.parser")
        soup = html.fromstring(str(soup))

        subject_categories = soup.xpath('//*[@id="search_subject_area"]/*/text()')[1:]
        subject_area = soup.xpath('//*[@id="search_subject_area"]/*/@value')[1:]

        subjects_dict = {}
        for index, sa in tqdm(enumerate(subject_area), total=len(subject_categories)):
            subject_area_ural = f'https://www.preprints.org/search?search_subject_area={sa}'
            req = requests.get(subject_area_ural)
            if req.status_code != 200:
                print(f'status | subject_dict.update | error with get soup (search_subject_area={sa}/{subject_categories[index]})')
            soup = bs4.BeautifulSoup(req.text, "html.parser")
            soup = html.fromstring(str(soup))
            soup = soup.xpath('//*[@id="search_subject_sub_area"]/*/text()')[1:]
            subjects_dict[subject_categories[index]] = soup
        print('status | subject_dict.update | successfully')

        with open('subjects.json', 'w') as file:
            json.dump(subjects_dict, file)

    def get():
        with open('subjects.json', 'r') as file:
            subjects_dict = json.load(file)
        return subjects_dict


import telebot
from telebot import types

bot = telebot.TeleBot(settings.TEST_BOT_TOKEN)


@bot.message_handler(commands=['topics'])
def main_topics(message):
    global user_topics
    user_topics = list()

    markup = types.InlineKeyboardMarkup()
    for main_topic in list(subject_dict.get().keys()):
        markup.add(types.InlineKeyboardButton(main_topic, callback_data=f'main;{main_topic}'))
    bot.send_message(message.chat.id,
                     'Выбери тему:',
                     parse_mode='html',
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    call_back = call.data.split(';')
    if call_back[0] == 'main':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Выбрать все', callback_data=f'sub;all'))
        for sub_topic in subject_dict.get()[call_back[1]]:
            markup.add(types.InlineKeyboardButton(sub_topic, callback_data=f'sub;{sub_topic}'))
        back_button = types.InlineKeyboardButton('назад', callback_data=f'back;')
        end_button = types.InlineKeyboardButton('готово', callback_data=f'end;')
        markup.row(back_button, end_button)

        bot.edit_message_text(chat_id=call.from_user.id,
                              message_id=call.message.id,
                              text='Что именно тебе интересно?',
                              parse_mode='html',
                              reply_markup=markup)
    elif call_back[0] == 'sub':
        user_topics.append(call_back[1])

    elif call_back[0] == 'all':
        # сделать так, чтобы в список топиков записывались все имеющиеся
        pass

    elif call_back[0] == 'back':
        markup = types.InlineKeyboardMarkup()
        for main_topic in list(subject_dict.get().keys()):
            markup.add(types.InlineKeyboardButton(main_topic, callback_data=f'main;{main_topic}'))
        bot.edit_message_text(chat_id=call.from_user.id,
                              message_id=call.message.id,
                              text='Выбери тему:',
                              parse_mode='html',
                              reply_markup=markup)

    elif call_back[0] == 'end':
        bot.delete_message(chat_id=call.from_user.id, message_id=call.message.id)
        bot.send_message(chat_id=call.from_user.id,
                         text=f"Вы выбрали: {', '.join(user_topics)}",
                         parse_mode='html')





bot.polling(none_stop=True)