from background import keep_alive 
from scraper import get_df
import telebot  
import time
import settings
keep_alive()

token = settings.TEST_BOT_TOKEN
bot = telebot.TeleBot(token)  

chat_id = settings.ADMIN_CHAT_ID
i = 0
while True:
  df = get_df()
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