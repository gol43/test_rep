from aiogram.types import (ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton, BotCommand)
from aiogram.utils.keyboard import InlineKeyboardBuilder

import logging


cancel = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отмена⛔️", callback_data="cancel")]])

main_client = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Проверка IMEI'),
     KeyboardButton(text='Доступные серверы')],

    [KeyboardButton(text='white-list')]],
    resize_keyboard=True, input_field_placeholder='Выберите пункт меню')

async def set_main_bot_commands(bot):
    commands = [BotCommand(command="/start", description="Начать")]
    await bot.set_my_commands(commands)


async def inline_add_users(ALLOWED_USERS):
    try:
        add_user_kb = InlineKeyboardBuilder()
        if ALLOWED_USERS == []:
            add_user_kb.add(InlineKeyboardButton(text='Добавить пользователя ✨', callback_data='add_user'))
            add_user_kb.add(InlineKeyboardButton(text='Отмена ⛔️', callback_data='cancel'))
        else:
            add_user_kb.add(InlineKeyboardButton(text='Добавить пользователя ✨', callback_data='add_user'))
            add_user_kb.add(InlineKeyboardButton(text='Посмотреть список пользователей 👁', callback_data='get_user_list'))
            add_user_kb.add(InlineKeyboardButton(text='Отмена ⛔️', callback_data='cancel'))
        return add_user_kb.adjust(1).as_markup()
    except Exception as e:
        logging.error(f'Ошибка в inline_add_users {e}', exc_info=True)

async def inline_add_user_list(ALLOWED_USERS):
    try:
        add_user_list_kb = InlineKeyboardBuilder()
        for idx, admin in enumerate(ALLOWED_USERS):
            add_user_list_kb.add(
                InlineKeyboardButton(text=str(admin), callback_data=f'get_user:{idx}')
            )
        add_user_list_kb.add(InlineKeyboardButton(text='Отмена ⛔️', callback_data='cancel'))
        return add_user_list_kb.adjust(1).as_markup()
    except Exception as e:
        logging.error(f'Ошибка в inline_add_user_list {e}', exc_info=True)

delete_user_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Удалить пользователя 🗑️', callback_data='delete_user')],
    [InlineKeyboardButton(text='Отмена ⛔️', callback_data='cancel')],
])