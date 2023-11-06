import settings
import subjects
import users
import re
import telebot
from telebot import types

bot = telebot.TeleBot(settings.TEST_BOT_TOKEN)
user_topics = list()
all_topic = dict()
all_topic_ru = dict()


def back_to_main_subjects(call):
    global all_topic
    global all_topic_ru
    markup = types.InlineKeyboardMarkup()
    for mt_id, main_topic in enumerate(list(all_topic.keys())):
        markup.add(types.InlineKeyboardButton(all_topic_ru[mt_id], callback_data=f'main;{main_topic}'))
    markup.add(types.InlineKeyboardButton('готово', callback_data=f'end;'))
    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text='Выбери тему:',
                          parse_mode='html',
                          reply_markup=markup)


def print_sub_subject(call, subject):
    global all_topic
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Выбрать все', callback_data=f'all;{subject}'))
    sub_topic_ru = all_topic_ru[list(all_topic_ru.keys())[list(all_topic.keys()).index(subject)]]
    for st_id, sub_topic in enumerate(all_topic[subject]):
        markup.add(types.InlineKeyboardButton(sub_topic_ru[st_id], callback_data=f'sub;{subject};{sub_topic}'))
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
    global all_topic_ru

    user_topics = users.get_user_topic(message.from_user.id)
    all_topic = subjects.get()
    all_topic_ru = all_topic['translate']
    for topic_id, (k, v) in enumerate(all_topic['original'].items()):
        for t in v:
            if t in user_topics:
                # Ты остановился тут

    all_topic = {k: ['✅ ' + t if t in user_topics else t for t in v] }


    markup = types.InlineKeyboardMarkup()
    for main_topic in list(all_topic.keys()):
        markup.add(types.InlineKeyboardButton(main_topic, callback_data=f'main;{main_topic}'))
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
        print_sub_subject(call, call_back[1])

    elif call_back[0] == 'sub':
        if call_back[2][2:] in user_topics:
            user_topics.remove(call_back[2][2:])
            all_topic = eval(re.sub(call_back[2], call_back[2][2:], str(all_topic)))

        else:
            user_topics.append(call_back[2])
            all_topic = eval(re.sub(call_back[2], '✅ ' + call_back[2], str(all_topic)))

        print_sub_subject(call, call_back[1])

    elif call_back[0] == 'all':
        user_topics += all_topic[call_back[1]]
        for sub_topic in all_topic[call_back[1]]:
            all_topic = eval(re.sub(sub_topic, '✅ ' + sub_topic, str(all_topic)))
        print_sub_subject(call, call_back[1])

    elif call_back[0] == 'back':
        back_to_main_subjects(call)

    elif call_back[0] == 'end':
        bot.delete_message(chat_id=call.from_user.id, message_id=call.message.id)
        bot.send_message(chat_id=call.from_user.id,
                         text=f"Вы выбрали: {', '.join(user_topics)}",
                         parse_mode='html')

        users.add_user_topic(str(call.from_user.id), user_topics)


bot.polling(none_stop=True)
