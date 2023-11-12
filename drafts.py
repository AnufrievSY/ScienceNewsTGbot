import settings
import subjects
import users
import re
import telebot
from telebot import types

bot = telebot.TeleBot(settings.TEST_BOT_TOKEN)
user_topics = list()
all_topic = dict()


def back_to_main_subjects(call):
    global all_topic
    markup = types.InlineKeyboardMarkup()
    for id, main_topic in enumerate(list(all_topic['translate'].keys())):
        markup.add(types.InlineKeyboardButton(main_topic, callback_data=f'main;{id}'))
    markup.add(types.InlineKeyboardButton('готово', callback_data=f'end;'))

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text='Выбери тему:',
                          parse_mode='html',
                          reply_markup=markup)


def print_sub_subject(call, subject_id):
    global all_topic
    markup = types.InlineKeyboardMarkup()
    subject_name = list(all_topic["original"].keys())[subject_id]
    markup.add(types.InlineKeyboardButton('Выбрать все', callback_data=f'all;{subject_id}'))
    for st_id, sub_topic in enumerate(all_topic['original'][subject_name]):
        markup.add(types.InlineKeyboardButton(all_topic['translate'][list(all_topic['translate'].keys())[subject_id]][st_id], callback_data=f'sub;{subject_id};{st_id}'))
    back_button = types.InlineKeyboardButton('назад', callback_data=f'back;')
    end_button = types.InlineKeyboardButton('готово', callback_data=f'end;')
    markup.row(back_button, end_button)

    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text='Что именно тебе интересно?',
                          parse_mode='html',
                          reply_markup=markup)


@bot.message_handler(commands=['topics'])
def main_topics(message):
    global all_topic
    global user_topics

    user_topics = users.get_user_topic(message.from_user.id)
    all_topic = subjects.get()
    for index_1, key in enumerate(list(all_topic['original'].keys())):
        for index_2, value in enumerate(all_topic['original'][key]):
            if value in user_topics:
                all_topic['translate'][list(all_topic['translate'].keys())[index_1]][index_2] = '✅ '+all_topic['translate'][list(all_topic['translate'].keys())[index_1]][index_2]

    markup = types.InlineKeyboardMarkup()
    for id, main_topic in enumerate(list(all_topic['translate'].keys())):
        markup.add(types.InlineKeyboardButton(main_topic, callback_data=f'main;{id}'))
    markup.add(types.InlineKeyboardButton('готово', callback_data=f'end;'))
    bot.send_message(message.chat.id,
                     'Выбери тему:',
                     parse_mode='html',
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global user_topics
    global all_topic
    call_back = call.data.split(';')
    if call_back[0] == 'main':
        print_sub_subject(call, int(call_back[1]))

    elif call_back[0] == 'sub':
        main_name_original = list(all_topic['original'].keys())[int(call_back[1])]
        main_name_translate = list(all_topic['translate'].keys())[int(call_back[1])]
        sub_name_original = all_topic['original'][main_name_original][int(call_back[2])]
        sub_name_translate = all_topic['translate'][main_name_translate][int(call_back[2])]

        if sub_name_original in user_topics:
            user_topics.remove(sub_name_original)
            all_topic['translate'][main_name_translate][int(call_back[2])] = sub_name_translate[2:]

        else:
            user_topics.append(sub_name_original)
            all_topic['translate'][main_name_translate][int(call_back[2])] = '✅ '+sub_name_translate

        print_sub_subject(call, int(call_back[1]))

    elif call_back[0] == 'all':
        main_name_original = list(all_topic['original'].keys())[int(call_back[1])]
        main_name_translate = list(all_topic['translate'].keys())[int(call_back[1])]

        for sub_topic_id, sub_topic_translate in enumerate(all_topic['translate'][main_name_translate]):
            if all_topic['original'][main_name_original][sub_topic_id] not in user_topics:
                user_topics.append(all_topic['original'][main_name_original][sub_topic_id])
                all_topic['translate'][main_name_translate][sub_topic_id] = '✅ ' + sub_topic_translate

        print_sub_subject(call, int(call_back[1]))

    elif call_back[0] == 'back':
        back_to_main_subjects(call)

    elif call_back[0] == 'end':
        bot.delete_message(chat_id=call.from_user.id, message_id=call.message.id)
        bot.send_message(chat_id=call.from_user.id,
                         text=f"Вы выбрали: {', '.join(user_topics)}",
                         parse_mode='html')

        users.add_user_topic(str(call.from_user.id), user_topics)


bot.polling(none_stop=True)
