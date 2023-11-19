import settings
import subjects
import users
import telebot
from telebot import types


bot = telebot.TeleBot(settings.TEST_BOT_TOKEN)
user_topics = list()
all_topic = dict()
bot_message_id = int()
chat_id = int()


def print_sub_subject(call, subject_id):
    """
    Функция, которая организует работу с вторичными предметами той или иной науки.
    По итогу в чате с ботом, последнее отправленное ботом сообщение будет изменено
    на список предметов в выбранной группе наук.

    Параметры:
    call (telebot.types.CallbackQuery): элемент содержащий информацию о нажатой клавише
    subject_id (int): номер категории наук, предметы которой надо вернуть
    """

    # Подгружаем уже словарь с имеющимися на сайте темами
    global all_topic
    # Определяем переменную для создания кнопок
    markup = types.InlineKeyboardMarkup()
    # Получаем список тем, определенной категории наук на основании переданного subject_id
    subject_name = list(all_topic["original"].keys())[subject_id]
    # Создаем кнопку для возможности выбора сразу всех вариантов
    markup.add(types.InlineKeyboardButton('Выбрать все', callback_data=f'all;{subject_id}'))
    # Создаем свою кнопку для каждой науки
    for st_id, sub_topic in enumerate(all_topic['original'][subject_name]):
        markup.add(
            types.InlineKeyboardButton(
                # В качестве текста для кнопки берем заранее переведенные их значения
                all_topic['translate'][list(all_topic['translate'].keys())[subject_id]][st_id],
                # В качестве обратной связи от кнопки определяем:
                # sub - условное обозначение, что это именно ПОД-тема в классе наук
                # subject_id - номер, к которому относится класс науки
                # st_id = номер темы в классе наук
                callback_data=f'sub;{subject_id};{st_id}'))
    # Создаем кнопку для возможности возврата ко всем классам наук
    back_button = types.InlineKeyboardButton('назад', callback_data=f'back;')
    # Создаем кнопку завершения работы с выбором любимых тематик
    end_button = types.InlineKeyboardButton('готово', callback_data=f'end;')
    # Добавляем кнопку возврата и завершения как одну строчку, а не друг под другому
    markup.row(back_button, end_button)
    # Меняем последнее сообщение бота
    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.id,
                          text='Что именно тебе интересно?',
                          parse_mode='html',
                          reply_markup=markup)


@bot.message_handler(commands=['topics'])
def main_topics(message=None):
    """
    Функция для обработки команды /topics

    По итогу будет произведена запись или изменение любимых тем пользователя, которые
    он хотел бы получать.
    """
    global all_topic, user_topics, bot_message_id, chat_id

    if message:
        chat_id = message.from_user.id
        user_topics = users.get_user_topic(chat_id)
        all_topic = subjects.get(user_topics)

    markup = types.InlineKeyboardMarkup()
    for topic_id, main_topic in enumerate(list(all_topic['translate'].keys())):
        markup.add(types.InlineKeyboardButton(main_topic, callback_data=f'main;{topic_id}'))
    markup.add(types.InlineKeyboardButton('готово', callback_data=f'end;'))

    if message:
        bot.send_message(chat_id,
                         'Выбери тему:',
                         parse_mode='html',
                         reply_markup=markup)
        bot_message_id = message.message_id + 1

    else:
        bot.edit_message_text(chat_id=chat_id,
                              message_id=bot_message_id,
                              text='Выбери тему:',
                              parse_mode='html',
                              reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    """
    Функция обратной связи для созданных кнопок
    main - возвращает под-темы имеющиеся в переданном классе наук
    sub - производит добавление или удаление выбранной под-темы из
        списка любых тем пользователя
    all - позволяет сразу выбрать или отменить выбор всех переданных под-тем
    back - возвращает пользователя к списку всех классов наук
    end - завершает работу с любимыми темами и сохраняет их в словарь с данными
        обо всех пользователях
    """
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
        main_topics()

    elif call_back[0] == 'end':
        bot.delete_message(chat_id=call.from_user.id, message_id=call.message.id)
        bot.send_message(chat_id=call.from_user.id,
                         text=f"Вы выбрали: {', '.join(user_topics)}",
                         parse_mode='html')

        users.add_user_topic(str(call.from_user.id), user_topics)


bot.polling(none_stop=True)
