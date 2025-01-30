from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from dotenv import load_dotenv
from fastapi import HTTPException, FastAPI

import app.redis as rd
from app.keyboards import main_client, cancel, delete_user_kb, inline_add_users, inline_add_user_list
from app.request_helper import get_service_id, check_imei

import logging
import json
import os

load_dotenv()

API_TOKEN_SANDBOX = os.getenv("API_TOKEN_SANDBOX")

app = FastAPI()
router = Router()

ALLOWED_USERS = []
PASSWORD_FOR_ADD_ALLOWED_USERS = '123'

class Imei(StatesGroup):
    number = State()

class Allow_User(StatesGroup):
    user = State()

class Super_User_Password(StatesGroup):
    pwd = State()

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    try:
        await state.clear()
        user_tg_id = message.from_user.id
        bot_id_redis = message.bot.id
        last_message_id = await rd.get_user_message(user_tg_id, bot_id_redis)
        if last_message_id:
            await message.bot.delete_message(chat_id=user_tg_id, message_id=last_message_id)
            await rd.del_data(user_tg_id, bot_id_redis)
        msg = await message.answer("👋 Привет! Я помогу вам проверить IMEI устройства, и выдам вам необохдимую информацию. 📱",reply_markup=main_client)
        await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
    except Exception as e:
        logging.error(f'Ошибка в start_command {e}', exc_info=True)


@router.message(F.text == 'Проверка IMEI')
async def start_check_imei(message: Message, state: FSMContext):
    try:
        user_tg_id = message.from_user.id
        bot_id_redis = message.bot.id
        last_message_id = await rd.get_user_message(user_tg_id, bot_id_redis)
        await message.bot.delete_message(chat_id=user_tg_id, message_id=last_message_id)
        await rd.del_data(user_tg_id, bot_id_redis)

        if message.from_user.id not in ALLOWED_USERS:
            msg = await message.answer("У вас нет доступа к этому боту.", reply_markup=main_client)
            await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
            return
        msg = await message.answer("Отправьте IMEI проверки.", reply_markup=cancel)
        await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
        await state.set_state(Imei.number)
    except Exception as e:
        logging.error(f'Ошибка в start_check_imei {e}', exc_info=True)


@router.message(Imei.number)
async def handle_imei(message: Message, state: FSMContext):
    try:
        user_tg_id = message.from_user.id
        bot_id_redis = message.bot.id
        last_message_id = await rd.get_user_message(user_tg_id, bot_id_redis)
        await message.bot.delete_message(chat_id=user_tg_id, message_id=last_message_id)
        await rd.del_data(user_tg_id, bot_id_redis)
        await state.clear()
        imei = message.text.strip()

        if not (8 <= len(imei) <= 15) or not imei.isalnum():
            msg = await message.answer("Некорректный IMEI или серийный номер. Введите от 8 до 15 символов (цифры или буквы).", reply_markup=main_client)
            await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
            return

        data = await check_imei(imei)

        if data is None:
            msg = await message.answer("Ошибка при проверке IMEI.")
            await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
        else:
            formatted_data = json.dumps(data, indent=2)
            msg = await message.answer(f"Результат:\n<pre>{formatted_data}</pre>", parse_mode="HTML", reply_markup=main_client)
            await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
    except Exception as e:
        logging.error(f'Ошибка в handle_imei {e}', exc_info=True)


@app.post("/api/check-imei")
async def api_check_imei(imei: str, token: str):
    if token != API_TOKEN_SANDBOX:
        raise HTTPException(status_code=403, detail="Неверный токен.")
    
    if not (8 <= len(imei) <= 15) or not imei.isalnum():
        raise HTTPException(status_code=400, detail="Некорректный IMEI или серийный номер. Введите от 8 до 15 символов (цифры или буквы).")
    
    data = await check_imei(imei)

    if data is None:
        raise HTTPException(status_code=500, detail="Ошибка проверки IMEI.")
    
    return {"Результат": data}


@router.message(F.text == 'Доступные серверы')
async def start_check_imei(message: Message, state: FSMContext):
    try:
        await state.clear()
        user_tg_id = message.from_user.id
        bot_id_redis = message.bot.id
        last_message_id = await rd.get_user_message(user_tg_id, bot_id_redis)
        await message.bot.delete_message(chat_id=user_tg_id, message_id=last_message_id)
        await rd.del_data(user_tg_id, bot_id_redis)

        if message.from_user.id not in ALLOWED_USERS:
            msg = await message.answer("У вас нет доступа к этому боту.", reply_markup=main_client)
            await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
            return

        service_id = await get_service_id()
        msg = await message.answer(f"На данный момент доступны следующие серверы для проверки IMEI:\n\n{'; '.join(service_id)}", reply_markup=main_client)
        await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
    except Exception as e:
        logging.error(f'Ошибка в start_check_imei {e}', exc_info=True)


@router.message(F.text == 'white-list')
async def allowed_users(message: Message, state: FSMContext):
    try:
        user_tg_id = message.from_user.id
        bot_id_redis = message.bot.id
        last_message_id = await rd.get_user_message(user_tg_id, bot_id_redis)
        await message.bot.delete_message(chat_id=user_tg_id, message_id=last_message_id)
        await rd.del_data(user_tg_id, bot_id_redis)

        msg = await message.answer(f'Введите пароль:\n\n(Пароль: 123)', reply_markup=cancel)
        await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
        await state.set_state(Super_User_Password.pwd)
    except Exception as e:
        logging.error(f'Ошибка в allowed_users {e}', exc_info=True)

@router.message(Super_User_Password.pwd)
async def catch_pwd(message: Message, state: FSMContext):
    try:
        await state.clear()
        bot_id_redis = message.bot.id
        user_tg_id = message.from_user.id
        last_message_id = await rd.get_user_message(user_tg_id, bot_id_redis)
        await message.bot.delete_message(chat_id=message.chat.id, message_id=last_message_id)
        await rd.del_data(user_tg_id, bot_id_redis)

        if message.text == PASSWORD_FOR_ADD_ALLOWED_USERS:
            msg = await message.answer(f'Здесь можно добавить пользователя в white-list, чтобы он мог пользоваться ботом!',
                                       reply_markup=await inline_add_users(ALLOWED_USERS))
            await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
        else:
            msg = await message.answer('Пароль неверный! Пока', reply_markup=main_client)
            await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
    except Exception as e:
        logging.error(f'Ошибка в catch_pwd {e}', exc_info=True)

@router.callback_query(F.data == 'add_user')
async def update_allowed_users(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer('')
        user_tg_id = callback.from_user.id
        bot_id_redis = callback.bot.id
        last_message_id = await rd.get_user_message(user_tg_id, bot_id_redis)
        await callback.bot.delete_message(chat_id=user_tg_id, message_id=last_message_id)
        await rd.del_data(user_tg_id, bot_id_redis)

        msg = await callback.message.answer(f'Перешлите сюда сообщение пользователя!', reply_markup=cancel)
        await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
        await state.set_state(Allow_User.user)
    except Exception as e:
        logging.error(f'Ошибка в allowed_users {e}', exc_info=True)

@router.message(Allow_User.user)
async def save_add_user(message: Message, state: FSMContext):
    try:
        await state.clear()
        bot_id_redis = message.bot.id
        user_tg_id = message.from_user.id
        last_message_id = await rd.get_user_message(user_tg_id, bot_id_redis)
        await message.bot.delete_message(chat_id=message.chat.id, message_id=last_message_id)
        await rd.del_data(user_tg_id, bot_id_redis)

        if message.forward_from is None:
            msg = await message.answer("⚠️ Пожалуйста, убедитесь, что вы пересылаете сообщение от пользователя, у которого разрешена пересылка сообщений!.",
                                        reply_markup=main_client)
            await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
            return

        forwarded_user_tg_id = message.forward_from.id
        forwarded_first_name = message.forward_from.first_name
        if forwarded_user_tg_id in ALLOWED_USERS:
            msg = await message.answer(f'Этот пользователь уже находится в white-list:\n{ALLOWED_USERS}', reply_markup=main_client)
            await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
            return
        ALLOWED_USERS.append(forwarded_user_tg_id)
        msg = await message.answer(f'<b><i>Вы успешно добавили пользователя в white-list:</i></b>\n\n👤Имя: <b>{forwarded_first_name}</b>\n🆔TG_ID:<b>{forwarded_user_tg_id}</b>\n\n'
                                   f'Список пользователей, которые теперь могут пользоваться ботом: {ALLOWED_USERS}', 
                                   reply_markup=main_client,
                                   parse_mode='HTML')
        await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
    except Exception as e:
        logging.error(f'Ошибка в save_add_user {e}', exc_info=True)

@router.callback_query(F.data == 'get_user_list')
async def get_user_list(callback: CallbackQuery, state: FSMContext):
    try:
        user_tg_id = callback.from_user.id
        bot_id_redis = callback.bot.id
        last_message_id = await rd.get_user_message(user_tg_id, bot_id_redis)
        await callback.bot.delete_message(chat_id=user_tg_id, message_id=last_message_id)
        await rd.del_data(user_tg_id, bot_id_redis)

        msg = await callback.message.answer(f'📋Вот список юзеров, которые могут пользоваться ботом👇', reply_markup=await inline_add_user_list(ALLOWED_USERS))
        await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
    except Exception as e:
        logging.error(f'Ошибка в get_user_list {e}', exc_info=True)

@router.callback_query(F.data.startswith('get_user:'))
async def select_user_button(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer('')
        bot_id_redis = callback.bot.id
        user_tg_id = callback.from_user.id
        last_message_id = await rd.get_user_message(user_tg_id, bot_id_redis)
        await callback.bot.delete_message(chat_id=user_tg_id, message_id=last_message_id)
        await rd.del_data(user_tg_id, bot_id_redis)

        user_id = int(callback.data.split(':')[1])
        await rd.set_hello_field(user_tg_id, bot_id_redis, 'add_user_id', user_id)

        msg = await callback.message.answer(f'Выберите действие с этим пользователем: 🆔 Telegram_id: {ALLOWED_USERS[user_id]}',
                                            reply_markup=delete_user_kb)
        await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
    except Exception as e:
        logging.error(f"Ошибка в select_user_button: {e}", exc_info=True)

@router.callback_query(F.data == 'delete_user')
async def delete_user_button(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer('')
        user_tg_id = callback.from_user.id
        bot_id_redis = callback.bot.id
        last_message_id = await rd.get_user_message(user_tg_id, bot_id_redis)
        await callback.bot.delete_message(chat_id=user_tg_id, message_id=last_message_id)
        await rd.del_data(user_tg_id, bot_id_redis)

        user_id = await rd.get_hello_field(user_tg_id, bot_id_redis, 'add_user_id')
        ALLOWED_USERS.pop(user_id)
        msg = await callback.message.answer(f'✅ Администратор успешно удалён.', reply_markup=main_client)
        await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка в delete_user_button: {e}", exc_info=True)


@router.callback_query(F.data == 'cancel')
async def cancel_button(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer('')
        await state.clear()
        user_tg_id = callback.from_user.id
        bot_id_redis = callback.bot.id
        last_message_id = await rd.get_user_message(user_tg_id, bot_id_redis)
        await callback.bot.delete_message(chat_id=user_tg_id, message_id=last_message_id)
        await rd.del_data(user_tg_id, bot_id_redis)
        msg = await callback.message.answer(f'Отмена операции', reply_markup=main_client)
        await rd.set_user_message(user_tg_id, msg.message_id, bot_id_redis)
    except Exception as e:
        logging.error(f'Ошибка в cancel_button {e}', exc_info=True)