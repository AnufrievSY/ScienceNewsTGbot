import json
import os


# Функция для добавления нового ключа пользователя
def add_user_key(chat_id, user_name):
    chat_id = str(chat_id)
    # Загрузка существующих данных из файла
    if os.path.isfile('user_keys.json') and os.path.getsize('user_keys.json') > 0:
        with open('user_keys.json', 'r') as file:
            data = json.load(file)
    else:
        data = {}
    # Добавление нового ключа пользователя
    if user_name is None and chat_id not in data.keys():
        user_name_list = [i for i in data.values() if i.startswith('user')]
        if len(user_name_list) == 0:
            user_name = 'user1'
        else:
            user_name_list.sort()
            user_name = 'user' + str(int(user_name_list[-1][4:]) + 1)
    elif user_name is None and chat_id in data.keys():
        user_name = data[chat_id]
    data[chat_id] = user_name

    # Сохранение обновленных данных в файл
    with open('user_keys.json', 'w') as file:
        json.dump(data, file)


# Функция для извлечения ключа пользователя
def get_user_key():
    # Загрузка данных из файла
    with open('user_keys.json', 'r') as file:
        data = json.load(file)

    # Получение ключа пользователя (если есть)
    key_list = list(data.keys())
    return key_list
