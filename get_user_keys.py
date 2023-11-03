import json
import os
import pandas as pd


# Функция для добавления нового ключа пользователя
def update_users(chat_id, user_name, last_message_id):
  chat_id = str(chat_id)
  # Загрузка существующих данных из файла
  if os.path.isfile(
      'user_keys.json') and os.path.getsize('user_keys.json') > 0:
    with open('user_keys.json', 'r') as file:
      data = json.load(file)
  else:
    data = {}
  # Добавление нового ключа пользователя
  if user_name is None and chat_id not in data.keys():
    data_df = pd.DataFrame.from_dict(data, orient='index')
    user_name_list = [
        i for i in data_df.user_name.tolist() if i.startswith('user')
    ]
    if len(user_name_list) == 0:
      user_name = 'user1'
    else:
      user_name_list.sort()
      user_name = 'user' + str(int(user_name_list[-1][4:]) + 1)
  elif user_name is None and chat_id in data.keys():
    user_name = data[chat_id]
  data[chat_id] = {"user_name": user_name, "last_message_id": last_message_id}

  # Сохранение обновленных данных в файл
  with open('user_keys.json', 'w') as file:
    json.dump(data, file)


# Функция для извлечения ключа пользователя
def get_users():
  # Загрузка данных из файла
  with open('user_keys.json', 'r') as file:
    data = json.load(file)

  # Получение ключей пользователя и их последних новостей
  df = pd.DataFrame.from_dict(data, orient='index')

  return df.last_message_id.to_dict()

# Функция для обновления последней новости пользователя
def update_last_news(chat_id, last_message_id):
  with open('user_keys.json', 'r') as file:
    data = json.load(file)
  data[str(chat_id)]["last_message_id"] = last_message_id
  with open('user_keys.json', 'w') as file:
    json.dump(data, file)