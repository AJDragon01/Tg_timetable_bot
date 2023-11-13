from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext, CommandHandler, ConversationHandler,
    MessageHandler, filters,  Application, CallbackQueryHandler,
)
from datetime import datetime, timedelta
import calendar
from databases import Database
from .database import DatabaseManager
import os
import json

db_manager = DatabaseManager('/Users/egorov_y/Tg_timetable_bot/Timetable.db')

# Определяем состояния для ConversationHandler
WORK_LOCATIONS = ['HQ', 'SDC', 'LDC', 'SEDC', 'MDC']
CHOOSING_USER, CHOOSING_LOCATION, TYPING_DATE, TYPING_START_TIME, TYPING_END_TIME, TYPING_DATE_FOR_VIEW, DELETING_SHIFT = range(7)
TYPING_USER = 7
# Получение директории, где расположен текущий скрипт
current_dir = os.path.dirname(os.path.abspath(__file__))
# Путь к config.json относительно текущего скрипта
config_path = os.path.join(current_dir, 'config.json')

config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r') as config_file:
    config = json.load(config_file)
    authorized_users = config['authorized_users']   


async def choose_location(update, context):
    location = update.message.text
    if location in WORK_LOCATIONS:
        context.user_data['location'] = location
        await update.message.reply_text(
            f"Вы выбрали {location}. Теперь выберите работника:",
            reply_markup=work_location_keyboard()
        )
        return CHOOSING_USER
    else:
        await update.message.reply_text("Пожалуйста, выберите место работы из предложенных вариантов.")
        return CHOOSING_LOCATION



async def start_assign_shift(update: Update, context: CallbackContext):
    if update.message.from_user.id in authorized_users:
        users = ["Имя1", "Имя2", "Имя3"]  # Замените на реальные имена
        keyboard = [[InlineKeyboardButton(user, callback_data=user)] for user in users]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Выберите пользователя для назначения смены:', reply_markup=reply_markup)
        return CHOOSING_USER
    else:
        await update.message.reply_text('У вас нет прав для назначения смен.')
        return ConversationHandler.END
    
    
async def choose_user(update, context):
    query = update.callback_query
    await query.answer()
    chosen_user_id = query.data
    context.user_data['chosen_user_id'] = chosen_user_id
    await query.edit_message_text(text=f"Выбран пользователь с ID: {chosen_user_id}. Теперь выберите дату смены:")
    return TYPING_DATE


def create_calendar(year=None, month=None):
    # Устанавливаем значения по умолчанию для года и месяца, если они не были переданы
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month

    data_ignore = "IGNORE"
    keyboard = []
    # Первый ряд - Месяц и Год
    row = [InlineKeyboardButton(calendar.month_name[month] + " " + str(year), callback_data=data_ignore)]
    keyboard.append(row)
    # Второй ряд - Дни недели
    row = [InlineKeyboardButton(day, callback_data=data_ignore) for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]]
    keyboard.append(row)

    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row = [InlineKeyboardButton(" ", callback_data=data_ignore) if day == 0 else InlineKeyboardButton(str(day), callback_data=f"CALENDAR-{year}-{month}-{day}") for day in week]
        keyboard.append(row)
    # Последний ряд - Кнопки управления
    row = [
        InlineKeyboardButton("<", callback_data=f"PREV-MONTH-{year}-{month}"),
        InlineKeyboardButton(" ", callback_data=data_ignore),
        InlineKeyboardButton(">", callback_data=f"NEXT-MONTH-{year}-{month}")
    ]
    keyboard.append(row)

    return InlineKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


async def inline_calendar_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data

    if "IGNORE" in data:
        return

    if "CALENDAR" in data:
        _, year, month, day = data.split('-')
        chosen_date = datetime(int(year), int(month), int(day)).strftime('%Y-%m-%d')
        context.user_data['date'] = chosen_date
        await query.edit_message_text(text=f"Выбранная дата: {chosen_date}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Теперь введите время начала смены (HH:MM):",
            reply_markup=time_keyboard()
        )
        return TYPING_START_TIME
    
    elif "PREV-MONTH" in data or "NEXT-MONTH" in data:
        action, year, month = data.split('-')[0:3]
        year, month = int(year), int(month)
        if "PREV-MONTH" in data:
            month -= 1
            if month < 1:
                month = 12
                year -= 1
        elif "NEXT-MONTH" in data:
            month += 1
            if month > 12:
                month = 1
                year += 1
        await query.edit_message_text(
            text="Выберите дату:",
            reply_markup=create_calendar(year)
        )

# Клавиатура для выбора времени
def time_keyboard():
    times = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]
    # Разбиваем на строки по 4 элемента для удобства отображения
    time_buttons = [times[i:i + 4] for i in range(0, len(times), 4)]
    return ReplyKeyboardMarkup(time_buttons, one_time_keyboard=True, resize_keyboard=True)

# Клавиатура для выбора места работы
def work_location_keyboard():
    return ReplyKeyboardMarkup(
        [[location] for location in WORK_LOCATIONS], one_time_keyboard=True, resize_keyboard=True
    )

# Начальная точка диалога для добавления смены
async def start_add_shift(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Выберите место работы для добавления смены:",
        reply_markup=work_location_keyboard()
    )
    return CHOOSING_LOCATION

async def type_date(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Выберите дату смены:",
        reply_markup=create_calendar()  # Отправляем инлайн-календарь пользователю без аргументов
    )
    return TYPING_START_TIME



# Шаг для ввода времени начала смены
async def type_start_time(update: Update, context: CallbackContext):
    start_time = update.message.text
    context.user_data['start_time'] = start_time
    await update.message.reply_text(
        "Введите время начала смены (HH:MM):",
        reply_markup=time_keyboard()
    )
    return TYPING_END_TIME

def is_valid_time(time_str):
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False
    
def create_shift(user_data):
    # Ваш код для создания смены на основе данных из user_data
    pass

# Шаг для ввода времени окончания смены
# Используйте эту функцию для проверки валидности введенного времени
async def type_end_time(update: Update, context: CallbackContext):
    end_time = update.message.text
    if not is_valid_time(end_time):
        await update.message.reply_text(
            "Время введено некорректно. Пожалуйста, введите время окончания смены в формате HH:MM.",
            reply_markup=time_keyboard()
        )
        return TYPING_END_TIME

    if not is_valid_time(context.user_data['start_time']):
        await update.message.reply_text(
            "Время начала смены введено некорректно. Пожалуйста, введите время начала смены в формате HH:MM.",
            reply_markup=time_keyboard()
        )
        return TYPING_START_TIME

    start_datetime = datetime.strptime(context.user_data['start_time'], '%H:%M')
    end_datetime = datetime.strptime(end_time, '%H:%M')

    if end_datetime <= start_datetime:
        await update.message.reply_text(
            "Время окончания смены должно быть позже времени начала смены. Пожалуйста, введите корректное время окончания.",
            reply_markup=time_keyboard()
        )
        return TYPING_END_TIME

    context.user_data['end_time'] = end_time

    # Вставьте фрагмент кода сюда
    create_shift(context.user_data)

    await update.message.reply_text(
        f"Смена успешно добавлена:\n"
        f"Место работы: {context.user_data['location']}\n"
        f"Пользователь: {context.user_data['user']}\n"
        f"Дата: {context.user_data['date']}\n"
        f"Время начала: {context.user_data['start_time']}\n"
        f"Время окончания: {context.user_data['end_time']}",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Очистим данные пользователя
    context.user_data.clear()

    return ConversationHandler.END


# Обработчик команды /cancel для прерывания диалога
async def cancel_add_shift(update: Update, context: CallbackContext):
    await update.message.reply_text("Добавление смены отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def view_schedule(update: Update, context: CallbackContext):
    date = update.message.text
    user_id = update.message.from_user.id
    
    # Получаем смены из базы данных
    shifts = db_manager.get_shifts_from_db(user_id=user_id, date=date)
    
    # Формируем ответ пользователю
    shifts_info = '\n'.join([f'ID: {shift[0]}, Место: {shift[2]}, Время: с {shift[4]} до {shift[5]}' for shift in shifts])
    reply_message = f'Смены на {date}:\n{shifts_info}' if shifts else 'Смен на эту дату нет.'
    
    await update.message.reply_text(reply_message)
    return ConversationHandler.END

# Создание ConversationHandler для добавления смены
add_shift_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('add', start_add_shift)],
    states={
        CHOOSING_USER: [CallbackQueryHandler(choose_user)],
        CHOOSING_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_location)],
        TYPING_DATE: [CallbackQueryHandler(inline_calendar_handler, pattern='^CALENDAR-.*|^PREV-MONTH-.*|^NEXT-MONTH-.*')],
        TYPING_START_TIME: [MessageHandler(filters.Regex('^\\d{2}:\\d{2}$'), type_start_time)],
        TYPING_END_TIME: [CallbackQueryHandler(inline_calendar_handler, pattern='^CALENDAR-.*|^PREV-MONTH-.*|^NEXT-MONTH-.*')],
        TYPING_DATE_FOR_VIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, view_schedule)]

    },
    fallbacks=[CommandHandler('cancel', cancel_add_shift)]
)
# Здесь будут другие обработчики, например, help_command, delete_shift, view_schedule


from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Загрузка конфигурационного файла."""
    try:
        with open('config.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"users": {}}

def save_config(config: Dict[str, Any]) -> None:
    """Сохранение конфигурационного файла."""
    with open('config.json', 'w') as file:
        json.dump(config, file, indent=4)

def update_user_data(user_id: int, name: str) -> None:
    """Обновление данных пользователя в конфигурационном файле."""
    config = load_config()
    if str(user_id) not in config["users"]:
        config["users"][str(user_id)] = {"name": name}
        save_config(config)

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update_user_data(user.id, user.full_name)  # или user.username, если он существует
    await update.message.reply_text('Привет! Я бот для планирования смен. Используйте команды для управления расписанием.')

async def help_command(update, context):
    await update.message.reply_text('Вот список команд: /add, /delete, /view')

async def start_view_schedule(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Пожалуйста, введите дату, чтобы посмотреть смены (например, YYYY-MM-DD):"
    )
    return TYPING_DATE_FOR_VIEW


async def start_delete_shift(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Пожалуйста, введите ID смены, которую вы хотите удалить:"
    )
    return DELETING_SHIFT

async def delete_shift(update: Update, context: CallbackContext):
    try:
        shift_id = int(update.message.text)
        # Вызов метода удаления смены из базы данных
        db_manager.remove_shift_from_db(shift_id=shift_id)
        await update.message.reply_text('Смена удалена.')
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите числовой ID смены.')
        return DELETING_SHIFT
    return ConversationHandler.END

view_schedule_handler = ConversationHandler(
    entry_points=[CommandHandler('view', start_view_schedule)],
    states={
        TYPING_DATE_FOR_VIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, view_schedule)]
    },
    fallbacks=[CommandHandler('cancel', cancel_add_shift)]
)

delete_shift_handler = ConversationHandler(
    entry_points=[CommandHandler('delete', start_delete_shift)],
    states={
        DELETING_SHIFT: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_shift)]
    },
    fallbacks=[CommandHandler('cancel', cancel_add_shift)]
)


async def start(update, context):
    await update.message.reply_text('Привет! Я бот для планирования смен. Используйте команды для управления расписанием.')
    user_id = update.message.from_user.id
    print(f"User ID: {user_id}")

async def help_command(update, context):
    await update.message.reply_text('Вот список команд: /add, /delete, /view')

# Добавляем обработчики /start и /help
start_handler = CommandHandler('start', start)
help_handler = CommandHandler('help', help_command)


__all__ = [
    'add_shift_conversation_handler',
    'view_schedule_handler',
    'delete_shift_handler',
    'start_handler',
    'help_handler',
    # Добавьте сюда другие обработчики, если они есть
]


