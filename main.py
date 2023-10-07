# from background import keep_alive
from scraper import get_df
import telebot  
import time
import settings
# keep_alive()

# Создание экземпляра бота
bot = telebot.TeleBot(settings.TEST_BOT_TOKEN)

# chat_id = settings.ADMIN_CHAT_ID


# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start"])
def start(message, res=False):
    chat_id = message.chat.id
    print('get new chat: ', chat_id)
    while True:
        df = get_df('test')
        if df.empty:
          pass
        else:
          # Текст сообщения
          for i in df.index:

            message_text = '\n'.join([f"[{df.loc[i,'Название'].upper()}]({df.loc[i,'Ссылка']})",
                                f"\n{' | '.join(df.loc[i,'Ключевые слова']+df.loc[i,'Науки']).lower()}\n",
                                df.loc[i,'Краткое описание'],
                                '\n'+', '.join(df.loc[i,'Авторы']),
                                df.loc[i,'Дата публикации']])
            bot.send_message(chat_id=chat_id, text=message_text, parse_mode="Markdown")

    time.sleep(5*60.0)

# Запускаем бота
bot.polling(none_stop=True, interval=0)


