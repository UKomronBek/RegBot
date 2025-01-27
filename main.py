import telebot
import json
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from text import *
from config import *
import logging



# Создаем бота с вашим токеном
API_TOKEN = TOKEN
bot = telebot.TeleBot(API_TOKEN)

# Telegram ID администраторов
ADMIN_IDS = [7393504121, 7232041443, 6052724492]
# 7393504121, 7232041443, 6052724492
# Путь к файлу базы данных
DB_FILE = "usersIHT_BotLab.json"

# Загружаем существующую базу данных или создаем новую
try:
    with open(DB_FILE, "r", encoding="utf-8") as f:
        users_db = json.load(f)
except FileNotFoundError:
    users_db = {}

# Временное хранилище данных пользователей в процессе регистрации
user_data = {}
# Список клубов и их владельцев
CLUBS = {
    "IHT BotLab": 7393504121,
    # "Speaking Club IHT": 7232041443,
    # "Media & Design": 7232041443
}

# Тексты информации для каждого клуба
club_info = {
    "IHT BotLab": infoIHT_BotLab,
    # "Speaking Club IHT": info_Speaking_Club_IHT,
    # "Media & Design": info_Media_and_Design
}


# Обработчики команд для каждого клуба
@bot.message_handler(commands=['infoIHT_BotLab'])
def info_IHT_BotLab(message):
    bot.send_message(message.chat.id, club_info["IHT BotLab"], parse_mode="HTML")

# @bot.message_handler(commands=['infoSpeaking_Club_IHT'])
# def info_Speaking_Club_IHT(message):
#     bot.send_message(message.chat.id, club_info["Speaking Club IHT"], parse_mode="HTML")
#
# @bot.message_handler(commands=['infoMedia_and_Design'])
# def info_Media_and_Design(message):
#     bot.send_message(message.chat.id, club_info["Media & Design"], parse_mode="HTML")


# Шаги регистрации
def ask_name(message):
    bot.send_message(message.chat.id, "Введите ваше имя:")
    bot.register_next_step_handler(message, ask_surname)

def ask_surname(message):
    # Проверка и инициализация данных
    if message.chat.id not in user_data:
        user_data[message.chat.id] = {}

    # Сохранение имени
    user_data[message.chat.id]["name"] = message.text
    bot.send_message(message.chat.id, "Введите вашу фамилию:")
    bot.register_next_step_handler(message, ask_group)


def ask_group(message):
    user_data[message.chat.id]["surname"] = message.text
    bot.send_message(message.chat.id, "Введите вашу учебную группу:")
    bot.register_next_step_handler(message, ask_phone)
def ask_phone(message):
    user_data[message.chat.id]["group"] = message.text
    username = user_data[message.chat.id].get("username", None)

    # Создание клавиатуры
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    phone_button = KeyboardButton(text="Поделиться номером телефона", request_contact=True)

    if username != "Не указано":  # Если username есть, добавляем кнопку "Не хочу делиться"
        no_phone_button = KeyboardButton(text="Не хочу делиться контактными данными")
        markup.add(phone_button, no_phone_button)
    else:
        markup.add(phone_button)

    bot.send_message(
        message.chat.id,
        "Пожалуйста, поделитесь вашим номером телефона или откажитесь.",
        reply_markup=markup
    )

# Обработчик получения контакта
@bot.message_handler(content_types=['contact'])
def save_contact(message):
    if message.contact is not None:
        user_data[message.chat.id]["phone"] = message.contact.phone_number
        save_user_data(message)  # Сохраняем данные пользователя

        # Удаляем клавиатуру после получения контакта
        bot.send_message(
            message.chat.id,
            "Для дополнительной информации о боте, существует команда \n/info",
            reply_markup=ReplyKeyboardRemove()  # Удаляем клавиатуру
        )
    else:
        # Удаляем клавиатуру в случае ошибки
        bot.send_message(
            message.chat.id,
            "Ошибка. Попробуйте снова /start.",
            reply_markup=ReplyKeyboardRemove()  # Удаляем клавиатуру
        )

# Обработчик отказа от контакта
@bot.message_handler(func=lambda message: message.text == "Не хочу делиться контактными данными")
def refuse_contact(message):
    username = user_data[message.chat.id].get("username", None)

    if username != "Не указано":  # Если у пользователя есть username, можно отказаться
        user_data[message.chat.id]["phone"] = "Не предоставлено"
        save_user_data(message)

        # Удаляем клавиатуру после отказа
        bot.send_message(
            message.chat.id,
            "Для дополнительной информации о боте, существует команда \n/info",
            reply_markup=ReplyKeyboardRemove()  # Удаляем клавиатуру
        )
    else:  # Если username нет, продолжаем запрашивать номер
        bot.send_message(
            message.chat.id,
            "Так как у вас нет username, пожалуйста, предоставьте номер телефона."
        )
        ask_phone(message)  # Запрашиваем номер телефона заново

def save_user_data(message):
    user_data[message.chat.id]["telegram_id"] = message.chat.id
    users_db[str(message.chat.id)] = user_data[message.chat.id]
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users_db, f, indent=4, ensure_ascii=False)

    # Отправка данных администраторам
    send_data_to_admin(user_data[message.chat.id])

    bot.send_message(
        message.chat.id, save_user_data_text_REG_TEST, parse_mode="HTML")

    # Удаляем временные данные
    user_data.pop(message.chat.id, None)

def send_data_to_admin(user_info):
    """Отправляет данные нового пользователя администраторам"""
    admin_message = (
        f"Новый пользователь зарегистрирован:\n"
        f"Имя: <code>{user_info['name']}</code>\n"
        f"Фамилия: <code>{user_info['surname']}</code>\n"
        f"Группа: <code>{user_info['group']}</code>\n"
        f"Номер телефона: +{user_info['phone']}\n"
        f"Telegram ID: <code>{user_info['telegram_id']}</code>\n"
        f"Username: @{user_info['username']}\n"
    )
    for admin_id in ADMIN_IDS:
        bot.send_message(admin_id, admin_message, parse_mode="HTML")

def send_existing_data(message, user_info):
    """Отправляет данные пользователя, если он уже зарегистрирован"""
    existing_message = (
        f"Вы уже зарегистрированы. Вот ваши данные:\n"
        f"Имя: <code>{user_info['name']}</code>\n"
        f"Фамилия: <code>{user_info['surname']}</code>\n"
        f"Группа: <code>{user_info['group']}</code>\n"
        f"Номер телефона: +{user_info['phone']}\n"
        f"Telegram ID: <code>{user_info['telegram_id']}</code>\n"
        f"Username: @{user_info['username']}\n"
    )
    bot.send_message(message.chat.id, existing_message, parse_mode="HTML")

@bot.message_handler(commands=['info'])
def start_message(message):
    bot.send_message(message.chat.id, info_text_message, parse_mode="HTML")

@bot.message_handler(commands=['policy'])
def start_message(message):
    bot.send_message(message.chat.id, policy, parse_mode="HTML")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_registration(message):
    telegram_id = str(message.chat.id)

    if telegram_id in users_db:
        send_existing_data(message, users_db[telegram_id])
        return

    # Инициализация записи в user_data
    user_data[message.chat.id] = {
        "telegram_id": telegram_id,
        "name": None,
        "surname": None,
        "group": None,
        "phone": None,
        "username": message.chat.username if message.chat.username else "Не указано",
    }

    bot.send_message(
        message.chat.id,
        f"Привет, <i>{message.chat.first_name}</i>!\n\n"
        f"Давайте проведём регистрацию на клуб <b>IHT BotLab</b>.\n"
        f"Нам нужно собрать некоторые данные, чтобы мы могли выйти с вами на связь. Давайте начнём!",
        parse_mode='HTML'
    )
    ask_name(message)



@bot.message_handler(commands=['choose_club'])
def choose_club(message):
    """Команда для вызова действия выбора клуба"""
    if str(message.chat.id) not in users_db:
        bot.send_message(message.chat.id, "Вы не зарегистрированы! Пожалуйста, сначала пройдите регистрацию с помощью команды /start.")
        return

    # Показать список клубов
    show_club_options(message)

def show_club_options(message):
    """Отправляет пользователю список клубов для выбора"""
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for club_name in CLUBS.keys():
        markup.add(KeyboardButton(text=club_name))
    bot.send_message(
        message.chat.id,
        "Выберите клуб, в который хотите подать заявку:",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, process_club_selection)

def process_club_selection(message):
    """Обрабатывает выбор клуба пользователем"""
    selected_club = message.text

    if selected_club not in CLUBS:
        bot.send_message(
            message.chat.id,
            "Неверный выбор. Пожалуйста, выберите клуб из списка."
        )
        show_club_options(message)  # Повторно показываем список
        return

    # Отправляем данные владельцу клуба
    club_owner_id = CLUBS[selected_club]
    user_info = users_db.get(str(message.chat.id), {})
    club_message = (
        f"Новая заявка в клуб {selected_club}:\n"
        f"Имя: {user_info.get('name', 'Не указано')}\n"
        f"Фамилия: {user_info.get('surname', 'Не указано')}\n"
        f"Группа: {user_info.get('group', 'Не указано')}\n"
        f"Номер телефона: +{user_info.get('phone', 'Не указано')}\n"
        f"Telegram ID: {user_info.get('telegram_id', 'Не указано')}\n"
        f"Username: @{user_info.get('username', 'Не указано')}\n"
    )

    bot.send_message(club_owner_id, club_message, parse_mode="HTML")

    # Уведомляем администратора
    for admin_id in ADMIN_IDS:
        bot.send_message(
            admin_id,
            f"<b>Для администрации</b>\n\nПользователь {user_info.get('name')}\nЮзернейм: @{user_info.get('username')}\nНомер телефона: +{user_info.get('phone')} \nГруппа: {user_info.get('group')}\nУспешно подал заявку в клуб {selected_club}. ",
            parse_mode="HTML"
        )

    # Уведомляем пользователя
    bot.send_message(
        message.chat.id,
        f"Вы успешно подали заявку в клуб <b>{selected_club}</b>. Ожидайте обратной связи! \n\n"
        f"Пока, вы можете узнать дополнительную информацию про этот клуб через команду:\n"
        f"/info{selected_club.replace(' ', '_')}",
        parse_mode="HTML"
    )


@bot.message_handler(commands=['list_users'])
def list_users(message):
    # Проверяем, является ли пользователь одним из администраторов
    if message.chat.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")
        return

    if not users_db:
        bot.send_message(message.chat.id, "Пока никто не зарегистрировался.")
        return

    # Формируем список пользователей
    user_list = "📋 *Список зарегистрированных пользователей:*\n\n"
    for idx, user in enumerate(users_db.values(), start=1):
        user_list += (
            f"{idx}. Имя: <code>{user.get('name', 'Не указано')}</code>\n"
            f"   Фамилия: <code>{user.get('surname', 'Не указано')}</code>\n"
            f"   Группа: <code>{user.get('group', 'Не указано')}</code>\n"
            f"   Номер телефона: +{user.get('phone', 'Не указано')}\n"
            f"   Telegram ID: <code>{user.get('telegram_id', 'Не указано')}</code>\n"
            f"  Username: @{user.get('username', 'Не указано')}\n\n"
        )

    # Отправляем список всем администраторам
    for admin_id in ADMIN_IDS:
        bot.send_message(admin_id, user_list, parse_mode="HTML")

logging.basicConfig(level=logging.INFO)
# Запуск бота
if __name__ == "__main__":
    print("Бот запущен и работает...")
    bot.polling(none_stop = True, interval = 0, timeout = 990000)
