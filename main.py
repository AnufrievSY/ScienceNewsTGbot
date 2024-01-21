# Для работы с телеграмм ботом
import pandas as pd
import telebot
# Для доступа к настройкам телеграмм бота
import settings
# Для работы со словарем пользователей
import users
# Для получения последних новостей из источника
from parser import get_df
# Для распараллеливания процессов
import threading
# Для паузы между процессами, чтобы не нагружать систему
import time
# Для работы с науками к которым относится новость
import subjects
# Для работы с кнопками бота
from telebot import types


bot = telebot.TeleBot(settings.TEST_BOT_TOKEN)
user_topics = list()
all_topic = dict()
bot_message_id = int()
chat_id = int()
user_data = dict()


def bot_func():
    # Функция, обрабатывающая команду /start
    @bot.message_handler(commands=["start"])
    def start(message):
        # Получаем номер чата и имя обратившегося пользователя
        chat_id, user_name = message.chat.id, message.from_user.username
        # Получаем последнюю новость и ее идентификатор
        last_news, last_message_id = get_df()
        # Превращаем в словарь для удобного использования
        last_news = last_news.iloc[0].to_dict()
        # Формируем сообщение
        message_text = '\n'.join([f"[{last_news['Название'].upper()}](<{last_news['Ссылка']}>)",
                                  f"\n{' | '.join(last_news['Ключевые слова'] + last_news['Науки']).lower()}\n",
                                  last_news['Краткое описание'],
                                  '\n' + ', '.join(last_news['Авторы']),
                                  last_news['Дата публикации']])

        # Отправляем сообщение в чат
        bot.send_message(chat_id=chat_id,
                         text=message_text,
                         parse_mode="Markdown",
                         disable_web_page_preview=True)
        # Записываем в JSON файл нового пользователя
        users.add_user(chat_id, user_name, last_message_id)

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
        subject_df = all_topic.loc[all_topic.type == 'sub'].loc[all_topic.main_id == subject_id]
        # Создаем свою кнопку для каждой науки
        for _, (st_id, sub_topic) in subject_df[['sub_id', 'translate']].iterrows():
            markup.add(
                types.InlineKeyboardButton(
                    # В качестве текста для кнопки берем заранее переведенные их значения
                    sub_topic,
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
        global all_topic, user_topics, bot_message_id, chat_id, user_data
        if message:
            # Прежде чем начать работать, удалим пользователя из словаря пользователей
            # чтобы рассылка не мешала работе
            chat_id = message.from_user.id
            user_topics = users.get_user_topic(chat_id)
            user_topics = user_topics if user_topics else []
            all_topic = subjects.get(user_topics)
            user_data = users.delete_user(chat_id)

        markup = types.InlineKeyboardMarkup()
        for _, (topic_id, main_topic) in all_topic.loc[all_topic.type == 'main', ['main_id', 'translate']].iterrows():
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
        global user_topics, all_topic, user_data
        call_back = call.data.split(';')
        if call_back[0] == 'main':
            print_sub_subject(call, int(call_back[1]))

        elif call_back[0] == 'sub':
            topic_id = f'{call_back[1]}.{call_back[2]}'
            if topic_id in user_topics:
                user_topics.remove(topic_id)
                all_topic.loc[
                    (all_topic.main_id == int(call_back[1])) &
                    (all_topic.sub_id == int(call_back[2])),
                    'translate'] = all_topic.loc[
                        (all_topic.main_id == int(call_back[1])) &
                        (all_topic.sub_id == int(call_back[2])),
                        'translate'].values[0][1:]
            else:
                user_topics.append(topic_id)
                all_topic.loc[
                    (all_topic.main_id == int(call_back[1])) &
                    (all_topic.sub_id == int(call_back[2])),
                    'translate'] = '✅' + all_topic.loc[
                        (all_topic.main_id == int(call_back[1])) &
                        (all_topic.sub_id == int(call_back[2])),
                        'translate']
            print_sub_subject(call, int(call_back[1]))
        elif call_back[0] == 'back':
            main_topics()

        elif call_back[0] == 'end':
            bot.delete_message(chat_id=call.from_user.id, message_id=call.message.id)
            bot.send_message(chat_id=call.from_user.id,
                             text="Любимые темы успешно записаны.",
                             parse_mode='html')
            users.add_user(call.from_user.id,
                           user_data['user_name'],
                           user_data['last_message_id'])
            users.add_user_topic(str(call.from_user.id), user_topics)

    # Запускаем бота
    bot.polling(none_stop=True)


def send_news():
    while True:
        data = users.get_users_last_news()
        if data:
            for chat_id, last_message_id in data.items():
                topics = users.get_user_topic(chat_id)
                print(chat_id, last_message_id)
                news, last_message_id = get_df(2, topics)

                if news.empty:
                    print('No favorite topics')
                    print('*'*100)
                    pass
                else:
                    for i in news.index:
                        message_text = '\n'.join([f"[{news.loc[i, 'Название'].upper()}]({news.loc[i, 'Ссылка']})",
                                                  f"\n{' | '.join(news.loc[i, 'Ключевые слова'] + news.loc[i, 'Науки']).lower()}\n",
                                                  news.loc[i, 'Краткое описание'],
                                                  '\n' + ', '.join(news.loc[i, 'Авторы']),
                                                  news.loc[i, 'Дата публикации']])

                        bot.send_message(chat_id=chat_id,
                                         text=message_text,
                                         parse_mode="Markdown",
                                         disable_web_page_preview=True)
                    users.user_update_last_news(chat_id, last_message_id)
                    print(f'Send {len(news)} news')
                    print('*' * 100)

            # time.sleep(5 * 60.0)
        time.sleep(10)


if __name__ == "__main__":
    # send_news_thread = threading.Thread(target=send_news)
    # bot_thread = threading.Thread(target=bot_func)
    #
    # # send_news_thread.start()
    # bot_thread.start()
    bot_func()
