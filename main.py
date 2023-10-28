# Для работы с телеграмм ботом
import telebot
# Для доступа к настройкам телеграмм бота
import settings
# Для работы со словарем пользователей
import get_user_keys
# Для получения последних новостей из источника
from scraper import get_df
# Для распараллеливания процессов
import threading
# Для паузы между процессами, чтобы не нагружать систему
import time


# Создание экземпляра бота
bot = telebot.TeleBot(settings.TEST_BOT_TOKEN)


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
        message_text = '\n'.join([f"[{last_news['Название'].upper()}]({last_news['Ссылка']})",
                                  f"\n{' | '.join(last_news['Ключевые слова'] + last_news['Науки']).lower()}\n",
                                  last_news['Краткое описание'],
                                  '\n' + ', '.join(last_news['Авторы']),
                                  last_news['Дата публикации']])
        # Отправляем сообщение в чат
        bot.send_message(chat_id=chat_id, text=message_text, parse_mode="Markdown")
        # Записываем в JSON файл нового пользователя
        get_user_keys.update_users(chat_id, user_name, last_message_id)
    # Запускаем бота
    bot.polling(none_stop=True)


def send_news():
    while True:
        for chat_id, last_message_id in get_user_keys.get_users().items():
            print(chat_id, last_message_id)
            news, last_message_id = get_df(last_message_id)
            if news.empty:
                pass
            else:
                for i in news.index:
                    message_text = '\n'.join([f"[{news.loc[i, 'Название'].upper()}]({news.loc[i, 'Ссылка']})",
                                              f"\n{' | '.join(news.loc[i, 'Ключевые слова'] + news.loc[i, 'Науки']).lower()}\n",
                                              news.loc[i, 'Краткое описание'],
                                              '\n' + ', '.join(news.loc[i, 'Авторы']),
                                              news.loc[i, 'Дата публикации']])
                    bot.send_message(chat_id=chat_id, text=message_text, parse_mode="Markdown")

        time.sleep(5 * 60.0)


if __name__ == "__main__":
    send_news_thread = threading.Thread(target=send_news)
    bot_thread = threading.Thread(target=bot_func)

    send_news_thread.start()
    bot_thread.start()
