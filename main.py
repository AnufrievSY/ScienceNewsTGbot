# from background import keep_alive
from scraper import get_df
import telebot
import time
import settings
import get_user_keys

# keep_alive()

# Создаем переменную для тестового запуска
TEST_RUN = True

# Создание экземпляра бота
bot = telebot.TeleBot(settings.TEST_BOT_TOKEN)

# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start"])
def start(message, res=False):
    # chat_id = settings.ADMIN_CHAT_ID
    # chat_id = message.chat.id
    get_user_keys.add_user_key(message.chat.id, message.from_user.username)

    while True:
        df = get_df('test') if TEST_RUN else get_df()
        if df.empty:
            pass
        else:
            # Текст сообщения
            for i in df.index:
                message_text = '\n'.join([f"[{df.loc[i, 'Название'].upper()}]({df.loc[i, 'Ссылка']})",
                                          f"\n{' | '.join(df.loc[i, 'Ключевые слова'] + df.loc[i, 'Науки']).lower()}\n",
                                          df.loc[i, 'Краткое описание'],
                                          '\n' + ', '.join(df.loc[i, 'Авторы']),
                                          df.loc[i, 'Дата публикации']])
                for chat_id in get_user_keys.get_user_key():
                    if TEST_RUN:
                        print(chat_id, ': send_message')
                    else:
                        bot.send_message(chat_id=chat_id, text=message_text, parse_mode="Markdown")

        if TEST_RUN:
            break
        else:
            time.sleep(5 * 60.0)


# Запускаем бота
bot.polling(none_stop=True, interval=0)
